import os
import json
from fastapi import FastAPI, Request
import pika
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables
load_dotenv()

def initialize_rabbitmq_connection():
    """Initialize and return a RabbitMQ connection."""
    credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_DEFAULT_USER'), os.environ.get('RABBITMQ_DEFAULT_PASS'))
    rabbitmq_host = os.environ.get('RABBITMQ_HOST')
    rabbitmq_port = os.environ.get('RABBITMQ_PORT')
    parameters = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    return connection

def send_message_to_rabbitmq(event_payload, connection, queue_name):
    """Send event payload message to RabbitMQ."""
    try:
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        message = json.dumps(event_payload)
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)
        print(f"Message sent to RabbitMQ: {message}")
        connection.close()
    except Exception as e:
        print(f"Failed to send message to RabbitMQ: {e}")

@app.post('/webhook/minio')
async def minio_webhook(request: Request):
    """Endpoint to receive MinIO event notifications."""
    data = await request.json()
    connection = initialize_rabbitmq_connection()

    # Send event payload to RabbitMQ
    if data['EventName'] == 's3:ObjectCreated:Put':      
        send_message_to_rabbitmq(data, connection, os.environ.get('RABBITMQ_QUEUE_UPLOADER'))
        return {"status": "success", "message": "Upload event sent to RabbitMQ"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)
