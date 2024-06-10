import os
import json
import pika
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from minio import Minio
from minio.error import S3Error
from minio.commonconfig import CopySource
from osgeo import gdal

app = FastAPI()

def initialize_minio_client():
    """Initialize and return a Minio client."""
    return Minio(
        os.environ.get('MINIO_HOST'),
        access_key=os.environ.get('MINIO_BUCKET_ACCESS_KEY'),
        secret_key=os.environ.get('MINIO_BUCKET_SECRET_KEY'),
        secure=False
    )

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
        copy_source = CopySource(bucket_name, object_name)
        metadata = {"x-amz-meta-" + key: json.dumps(value) if isinstance(value, dict) else str(value)
                    for key, value in metadata.items()}
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
    try:
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
    except Exception as e:
        print(f"Error getting raster stats: {e}")
        return None

@app.post('/init')
async def init():
    return JSONResponse(content={"status": "initialized"})

@app.post('/run')
async def run(request: Request):
    try:
        event = await request.json()
        event_payload = event.get("event", {})
        
        print(f"Received event payload: {event_payload}")
        
        records = event_payload.get("Records")
        if records is None or len(records) == 0:
            print("No Records found in event payload")
            return JSONResponse(content={"status": "error", "message": "No Records found in event payload"})
        
        # Extract bucket name and object key from the event
        record = records[0]
        s3_info = record.get("s3")
        if s3_info is None:
            print("No s3 information found in the first record")
            return JSONResponse(content={"status": "error", "message": "No s3 information found in the first record"})
        
        bucket = s3_info.get("bucket")
        if bucket is None:
            print("No bucket information found in the s3 info")
            return JSONResponse(content={"status": "error", "message": "No bucket information found in the s3 info"})
        
        bucket_name = bucket.get("name")
        if bucket_name is None:
            print("Bucket name is missing")
            return JSONResponse(content={"status": "error", "message": "Bucket name is missing"})
        
        object_info = s3_info.get("object")
        if object_info is None:
            print("No object information found in the s3 info")
            return JSONResponse(content={"status": "error", "message": "No object information found in the s3 info"})
        
        object_name = object_info.get("key")
        if object_name is None:
            print("Object key is missing")
            return JSONResponse(content={"status": "error", "message": "Object key is missing"})
        
        # Define local path to save the downloaded file
        local_path = f"/tmp/{object_name.split('/')[-1]}"
        
        # Initialize MinIO client
        minio_client = initialize_minio_client()
        
        # Download file from MinIO
        if download_file_from_minio(minio_client, bucket_name, object_name, local_path):
            # Get raster stats
            raster_info = get_raster_stats(local_path)
            if raster_info:
                # Upload metadata to MinIO
                upload_metadata_to_minio(minio_client, bucket_name, object_name, raster_info)
                
                return JSONResponse(content={"status": "success", "raster_info": raster_info})
            else:
                return JSONResponse(content={"status": "error", "message": "Failed to get raster info"})
        else:
            return JSONResponse(content={"status": "error", "message": "Failed to download file from MinIO"})
    except Exception as e:
        print(f"Unexpected error: {e}")
        return JSONResponse(content={"status": "error", "message": f"An unexpected error occurred: {e}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
