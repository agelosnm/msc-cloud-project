## Create Python virtual environments for each component

```bash
cd metadata-extractor 
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```bash
cd invoker 
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## .env files adjustment
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


#### Install Java & Node.js
```
sudo apt install openjdk-8-jdk nodejs npm -y
```

#### Clone repo
```
git clone https://github.com/apache/openwhisk.git 
cd openwhisk 
```

#### Create .jar
```
./gradlew :core:standalone:build
```

#### Execute .jar
```
sudo java -Dwhisk.standalone.host.name=0.0.0.0 -Dwhisk.standalone.host.internal=127.0.0.1 -Dwhisk.standalone.host.external=0.0.0.0 -jar ./bin/openwhisk-standalone.jar --couchdb --kafka --api-gw --kafka-ui
```

Then test if the API is working at `http://localhost:3233/`

### Authentication
```
wsk property set \
  --apihost 'http://localhost:3233' \
  --auth '23bc46b1-71f6-4ed5-8c54-816aa4f8c502:123zO3xZCLrMN6v2BKK1dXYFpXlPkccOFqm12CdAsMgRU4VrNZ9lyGVCGuMDGIwP'
```

### Create action

#### Example JavaScript function

```js
function main(params) {
    console.log('Hello World');
    return {msg:'Hello '+params.name};
   }
```

#### Create action
```
wsk -i action create helloLab ../helloLab.js
```

#### Invoke action
```
wsk -i action invoke helloLab -b -p name "milko_cup"
```
Response:
```
ok: invoked /_/helloLab with id a0d8921b48c64a3a98921b48c65a3a8b
{
    "activationId": "a0d8921b48c64a3a98921b48c65a3a8b",
    "annotations": [
        {
            "key": "path",
            "value": "guest/helloLab"
        },
        {
            "key": "waitTime",
            "value": 220
        },
        {
            "key": "kind",
            "value": "nodejs:20"
        },
        {
            "key": "timeout",
            "value": false
        },
        {
            "key": "limits",
            "value": {
                "concurrency": 1,
                "logs": 10,
                "memory": 256,
                "timeout": 60000
            }
        }
    ],
    "duration": 9,
    "end": 1717429497156,
    "logs": [],
    "name": "helloLab",
    "namespace": "guest",
    "publish": false,
    "response": {
        "result": {
            "msg": "Hello milko_cup"
        },
        "size": 25,
        "status": "success",
        "success": true
    },
    "start": 1717429497147,
    "subject": "guest",
    "version": "0.0.1"
}
```

```
wsk namespace list -v (get auth for API)

wsk action delete metadata-extractor

wsk -i action create metadata-extractor geostats/metadata-extractor/app.py --kind python:3.10

wsk activation list

wsk activation get 3da527d22bbc4868a527d22bbc686872
```
