import os
from os.path import join, dirname
from dotenv import load_dotenv
from osgeo import gdal
import json
from minio import Minio
from minio.error import S3Error
import tempfile

dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)

# MinIO configuration
minio_client = Minio(
    os.environ.get('MINIO_HOST'),  # MinIO server URL
    access_key=os.environ.get('MINIO_BUCKET_ACCESS_KEY'),
    secret_key=os.environ.get('MINIO_BUCKET_SECRET_KEY'),
    secure=False
)

bucket_name = os.environ.get('MINIO_BUCKET_NAME')
object_name = "SEN_soc.tif"

def download_file_from_minio(minio_client, bucket_name, object_name, local_path):
    try:
        minio_client.fget_object(bucket_name, object_name, local_path)
        print(f"File downloaded successfully: {local_path}")
    except S3Error as err:
        print(f"Failed to download file: {err}")
        return False
    return True

def get_raster_stats(raster_path):
    # Open the raster file
    dataset = gdal.Open(raster_path)

    if not dataset:
        print(f"Failed to open file: {raster_path}")
        return None

    raster_info = {
        "raster_file": raster_path,
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

    # Close the dataset
    dataset = None

    return raster_info

# Download the file to a temporary location
with tempfile.NamedTemporaryFile(delete=False) as temp_file:
    local_path = temp_file.name

if download_file_from_minio(minio_client, bucket_name, object_name, local_path):
    # Get raster stats
    raster_info = get_raster_stats(local_path)
    if raster_info:
        print(json.dumps(raster_info, indent=4))

# Clean up the temporary file
os.remove(local_path)