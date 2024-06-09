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
        os.environ.get('MINIO_HOST'),  # MinIO server URL
        access_key=os.environ.get('MINIO_BUCKET_ACCESS_KEY'),
        secret_key=os.environ.get('MINIO_BUCKET_SECRET_KEY'),
        secure=False
    )

def initialize_rabbitmq_connection():
    """Initialize and return a RabbitMQ connection."""
    credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_DEFAULT_USER'), os.environ.get('RABBITMQ_DEFAULT_PASS'))
    parameters = pika.ConnectionParameters(os.environ.get('RABBITMQ_HOST'), '/', credentials)
    connection = pika.BlockingConnection(parameters)
    return connection

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

def send_message_to_rabbitmq(raster_info, connection, queue_name):
    """Send raster info message to RabbitMQ."""
    try:
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        message = json.dumps(raster_info)
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)
        print(f"Message sent to RabbitMQ: {message}")
        connection.close()
    except Exception as e:
        print(f"Failed to send message to RabbitMQ: {e}")

@app.post('/init')
async def init():
    return JSONResponse(content={"status": "initialized"})

@app.post('/run')
async def run(request: Request):
    event = await request.json()
    event_payload = event.get("event", {})
    
    # Extract bucket name and object key from the event
    bucket_name = event_payload.get("Records")[0]["s3"]["bucket"]["name"]
    object_name = event_payload.get("Records")[0]["s3"]["object"]["key"]
    
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
            
            # Send raster info to RabbitMQ
            rabbitmq_connection = initialize_rabbitmq_connection()
            queue_name = os.environ.get('RABBITMQ_QUEUE_NAME')
            send_message_to_rabbitmq(raster_info, rabbitmq_connection, queue_name)
            
            return JSONResponse(content={"status": "success", "raster_info": raster_info})
        else:
            return JSONResponse(content={"status": "error", "message": "Failed to get raster info"})
    else:
        return JSONResponse(content={"status": "error", "message": "Failed to download file from MinIO"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
