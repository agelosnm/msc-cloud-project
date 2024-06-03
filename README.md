## Create a new Python environment for the application

```bash
python3 -m venv geostats
source geostats/bin/activate
pip install -r requirements.txt
```

## Components provision
```bash
cp .env.example .env
```

## MinIO

### Bucket policy

```json
{
 "Version": "2012-10-17",
 "Statement": [
  {
   "Effect": "Allow",
   "Action": [
    "s3:PutObject",
    "s3:GetBucketLocation",
    "s3:GetObject",
    "s3:ListBucket"
   ],
   "Resource": [
    "arn:aws:s3:::<bucket_name>",
    "arn:aws:s3:::<bucket_name>/*"
   ]
  }
 ]
}
```

The above policy is required in the bucket in order for the raster file to be downladed localy temporarily and then after the extraction of their stats those to can be put as the corresponding object's metadata.

## RabbitMQ

Once the raster stats have been extracted, those are being sent at a RabbitMQ queue.

Example payload:

```json

{
  "driver": {
    "short_name": "GTiff",
    "long_name": "GeoTIFF"
  },
  "size": {
    "x_size": 2760,
    "y_size": 1951,
    "band_count": 20
  },
  "projection": "GEOGCS[\"WGS 84\",DATUM[\"WGS_1984\",SPHEROID[\"WGS 84\",6378137,298.257223563,AUTHORITY[\"EPSG\",\"7030\"]],AUTHORITY[\"EPSG\",\"6326\"]],PRIMEM[\"Greenwich\",0,AUTHORITY[\"EPSG\",\"8901\"]],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]],AXIS[\"Latitude\",NORTH],AXIS[\"Longitude\",EAST],AUTHORITY[\"EPSG\",\"4326\"]]",
  "geotransform": {
    "origin": {
      "x": -17.542849475432416,
      "y": 16.69196085087124
    },
    "pixel_size": {
      "x": 0.0022460753986229824,
      "y": -0.0022460753986229824
    }
  },
  "bands": [
    {
      "band_number": 1,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 80.41588319280257,
        "std_dev": 52.27359099374456
      }
    },
    {
      "band_number": 2,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 80.34677136930574,
        "std_dev": 52.2691263933284
      }
    },
    {
      "band_number": 3,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 80.27062848522355,
        "std_dev": 52.25721996014859
      }
    },
    {
      "band_number": 4,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 80.13699792570338,
        "std_dev": 52.24806647980567
      }
    },
    {
      "band_number": 5,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 80.07868861291469,
        "std_dev": 52.25327925110363
      }
    },
    {
      "band_number": 6,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 80.03217855122412,
        "std_dev": 52.239215065976424
      }
    },
    {
      "band_number": 7,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.99271301958629,
        "std_dev": 52.224527213392996
      }
    },
    {
      "band_number": 8,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.94908542334551,
        "std_dev": 52.23111296631091
      }
    },
    {
      "band_number": 9,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.92175587942207,
        "std_dev": 52.228715760895376
      }
    },
    {
      "band_number": 10,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.8347700762371,
        "std_dev": 52.244195047098216
      }
    },
    {
      "band_number": 11,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.81122545189908,
        "std_dev": 52.25187218334891
      }
    },
    {
      "band_number": 12,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.81090218474823,
        "std_dev": 52.262189427299724
      }
    },
    {
      "band_number": 13,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.8261226798856,
        "std_dev": 52.28217815423128
      }
    },
    {
      "band_number": 14,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.79977640688506,
        "std_dev": 52.27764163927496
      }
    },
    {
      "band_number": 15,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.80799278036652,
        "std_dev": 52.281807618873614
      }
    },
    {
      "band_number": 16,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.78735756041131,
        "std_dev": 52.27018043588641
      }
    },
    {
      "band_number": 17,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.79169472805104,
        "std_dev": 52.283879405363116
      }
    },
    {
      "band_number": 18,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.6835618652519,
        "std_dev": 52.18609900827516
      }
    },
    {
      "band_number": 19,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.5459174052433,
        "std_dev": 52.082730983765394
      }
    },
    {
      "band_number": 20,
      "data_type": "Int16",
      "statistics": {
        "min": 10.0,
        "max": 210.0,
        "mean": 79.54985048894211,
        "std_dev": 52.09747031408071
      }
    }
  ]
}

```

This message then can be consumed from a consuming service for further process

## OpenWhisk

### `wsk` CLI

```
wget https://github.com/apache/openwhisk-cli/releases/download/1.2.0/OpenWhisk_CLI-1.2.0-linux-386.tgz
tar -xvzf OpenWhisk_CLI-1.2.0-linux-386.tgz 
sudo mv wsk /usr/local/bin/
```

### Standalone OpenWhisk

```
# Install Java & Node.js
sudo apt install openjdk-8-jdk nodejs npm -y

git clone https://github.com/apache/openwhisk.git 
cd openwhisk 

# Create .jar
./gradlew :core:standalone:build

# Execute .jar
sudo java -Dwhisk.standalone.host.name=0.0.0.0 -Dwhisk.standalone.host.internal=127.0.0.1 -Dwhisk.standalone.host.external=0.0.0.0 -jar ./bin/openwhisk-standalone.jar --couchdb --kafka --api-gw --kafka-ui
```

Then test if the API is working at `http://localhost:3233/`