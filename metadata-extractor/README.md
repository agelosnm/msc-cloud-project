## Local dev environment

### Create Python virtual environments

```bash
cd metadata-extractor 
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Create Docker environments (dev images)

`docker build . -f Dockerfile.dev -t "angelosnm/geostats-metadata-extractor:dev"`

`docker run -d -p5000:8080 -v ./:/app angelosnm/geostats-metadata-extractor:dev`