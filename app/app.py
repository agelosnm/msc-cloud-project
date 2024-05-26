import os
from os.path import join, dirname
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from osgeo import gdal
import json
from minio import Minio
from minio.error import S3Error
from minio.commonconfig import CopySource
import tempfile

app = FastAPI()

def load_env():
    """Load environment variables from a .env file."""
    dotenv_path = join(dirname(__file__), '../.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        raise FileNotFoundError(f".env file not found at {dotenv_path}")

def initialize_minio_client():
    """Initialize and return a Minio client."""
    return Minio(
        os.environ.get('MINIO_HOST'),  # MinIO server URL
        access_key=os.environ.get('MINIO_BUCKET_ACCESS_KEY'),
        secret_key=os.environ.get('MINIO_BUCKET_SECRET_KEY'),
        secure=False
    )

def process_uploaded_file(minio_client, bucket_name, object_name):
    """Process the uploaded file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        local_path = temp_file.name
        try:
            if download_file_from_minio(minio_client, bucket_name, object_name, local_path):
                raster_info = get_raster_stats(local_path)
                if raster_info:
                    # Upload metadata
                    upload_metadata_to_minio(minio_client, bucket_name, object_name, raster_info)
        finally:
            os.remove(local_path)

@app.post('/webhook/minio')
async def minio_webhook(request: Request):
    """Endpoint to receive MinIO event notifications."""
    data = await request.json()
    event = data.get('EventName')
    if event == 's3:ObjectCreated:Put':
        bucket_name = data['Records'][0]['s3']['bucket']['name']
        object_name = data['Records'][0]['s3']['object']['key']
        minio_client = initialize_minio_client()
        process_uploaded_file(minio_client, bucket_name, object_name)
    return 'OK'

def download_file_from_minio(minio_client, bucket_name, object_name, local_path):
    """Download a file from MinIO."""
    try:
        minio_client.fget_object(bucket_name, object_name, local_path)
        print(f"File downloaded successfully: {local_path}")
        return True
    except S3Error as err:
        print(f"Failed to download file: {err}")
        return False

def upload_metadata_to_minio(minio_client, bucket_name, object_name, metadata):
    """Upload metadata to an object in MinIO."""
    try:
        # Create the CopySource object
        copy_source = CopySource(bucket_name, object_name)
        
        # Prepare metadata for upload, prefixing with 'x-amz-meta-'
        metadata = {"x-amz-meta-" + key: json.dumps(value) if isinstance(value, dict) else str(value)
                    for key, value in metadata.items()}
        
        # Use the copy_object method to update metadata
        minio_client.copy_object(
            bucket_name,
            object_name,
            copy_source,
            metadata=metadata,
            metadata_directive="REPLACE"
        )
        print(f"Metadata uploaded successfully for {object_name}")
    except S3Error as err:
        print(f"Failed to upload metadata: {err}")

def get_raster_stats(raster_path):
    """Retrieve and return statistics of a raster file."""
    dataset = gdal.Open(raster_path)
    if not dataset:
        print(f"Failed to open file: {raster_path}")
        return None

    raster_info = {
        "driver": {
            "short_name": dataset.GetDriver().ShortName,
            "long_name": dataset.GetDriver().LongName
        },
        "size": {
            "x_size": dataset.RasterXSize,
            "y_size": dataset.RasterYSize,
            "band_count": dataset.RasterCount
        },
        "projection": dataset.GetProjection(),
        "geotransform": {}
    }

    geotransform = dataset.GetGeoTransform()
    if geotransform:
        raster_info["geotransform"] = {
            "origin": {
                "x": geotransform[0],
                "y": geotransform[3]
            },
            "pixel_size": {
                "x": geotransform[1],
                "y": geotransform[5]
            }
        }

    bands = []
    for band_number in range(1, dataset.RasterCount + 1):
        band = dataset.GetRasterBand(band_number)
        stats = band.GetStatistics(True, True)
        bands.append({
            "band_number": band_number,
            "data_type": gdal.GetDataTypeName(band.DataType),
            "statistics": {
                "min": stats[0],
                "max": stats[1],
                "mean": stats[2],
                "std_dev": stats[3]
            }
        })

    raster_info["bands"] = bands

    dataset = None
    return raster_info

if __name__ == "__main__":
    load_env()
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
