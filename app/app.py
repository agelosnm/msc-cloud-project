import os
from osgeo import gdal
import json

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

# Example usage
raster_path = 'app/data/raster.tif'
raster_info = get_raster_stats(raster_path)
if raster_info:
    print(json.dumps(raster_info, indent=4))
