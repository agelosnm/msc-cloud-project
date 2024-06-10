import os
import json
from fastapi import FastAPI, Request
import requests
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables
load_dotenv()

# OpenWhisk configuration
API_HOST = os.getenv('OPENWHISK_API_HOST')
NAMESPACE = os.getenv('OPENWHISK_NAMESPACE')
ACTION_NAME = os.getenv('OPENWHISK_ACTION_NAME')
AUTH_KEY = os.getenv('OPENWHISK_AUTH_KEY')

def invoke_openwhisk_action(event_payload):
    """Invoke OpenWhisk action with the given event payload."""
    url = f'{API_HOST}/api/v1/namespaces/{NAMESPACE}/actions/{ACTION_NAME}?blocking=true&result=true'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {AUTH_KEY}'
    }
    response = requests.post(url, headers=headers, data=json.dumps({'event': event_payload}))
    
    if response.status_code == 200:
        print('Action invoked successfully')
        return response.json()
    else:
        print('Failed to invoke action')
        print('Status code:', response.status_code)
        print('Response:', response.text)
        return None

@app.post('/webhook/minio')
async def minio_webhook(request: Request):
    """Endpoint to receive MinIO event notifications."""
    data = await request.json()
    print("Received MinIO event:", data)
    # Invoke OpenWhisk action with the event payload
    result = invoke_openwhisk_action(data)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)
