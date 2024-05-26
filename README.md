## Create a new Python environment for the application

```bash
python3 -m venv geostats
source geostats/bin/activate
pip install -r requirements.txt
```

## Components provision
cp .env.example .env

## MinIO

Read & download data policy

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