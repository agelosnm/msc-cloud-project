import os
import pika
import json
import threading
import requests
from dotenv import load_dotenv
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# OpenWhisk configuration
OPENWHISK_API_HOST = os.getenv('OPENWHISK_API_HOST')
OPENWHISK_NAMESPACE = os.getenv('OPENWHISK_NAMESPACE')
OPENWHISK_ACTION_NAME = os.getenv('OPENWHISK_ACTION_NAME')
OPENWHISK_AUTH_KEY = os.getenv('OPENWHISK_AUTH_KEY')

def invoke_openwhisk_action(payload, openwhisk_action):
    """Invoke OpenWhisk action with the given event payload."""
    url = f'{OPENWHISK_API_HOST}/api/v1/namespaces/{OPENWHISK_NAMESPACE}/actions/{openwhisk_action}?blocking=true&result=true'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {OPENWHISK_AUTH_KEY}'
    }
    response = requests.post(url, headers=headers, data=json.dumps({'event': payload}))
    
    if response.status_code == 200:
        print('Action invoked successfully')
        return response.json()
    else:
        print('Failed to invoke action')
        print('Status code:', response.status_code)
        print('Response:', response.text)
        return None

def initialize_rabbitmq_connection():
    """Initialize and return a RabbitMQ connection."""
    credentials = pika.PlainCredentials(os.environ.get('RABBITMQ_DEFAULT_USER'), os.environ.get('RABBITMQ_DEFAULT_PASS'))
    rabbitmq_host = os.environ.get('RABBITMQ_HOST')
    rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', 5672))  # Ensure the port is an integer and use default 5672 if not set
    parameters = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    return connection

def uploader_callback(ch, method, properties, body):
    message = json.loads(body)
    print(f"Received message from {os.environ.get('RABBITMQ_QUEUE_UPLOADER')} queue: {message}")
    invoke_openwhisk_action(message, 'metadata-extractor')
    # Process the message specifically for the uploader queue
    # ...
    ch.basic_ack(delivery_tag=method.delivery_tag)

def raw_data_callback(ch, method, properties, body):
    message = json.loads(body)
    print(f"Received message from {os.environ.get('RABBITMQ_QUEUE_RAW_DATA')} queue: {message}")
    invoke_openwhisk_action(message, 'report-generator')
    # Process the message specifically for the uploader queue
    # ...
    ch.basic_ack(delivery_tag=method.delivery_tag)


# def raw_data_callback(ch, method, properties, body):
#     message = json.loads(body)
#     print(f"Received message from {os.environ.get('RABBITMQ_QUEUE_RAW_DATA')} queue: {message}")
#     # API endpoint
#     url = "https://api.openai.com/v1/chat/completions"

#     # Request headers
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {OPENAI_API_KEY}"
#     }

#     # Request payload
#     payload = {
#         "model": "gpt-3.5-turbo",
#         "messages": [{"role": "user", "content": "can you give me a description of the below raster data? what does this mean for this .tiff file?" + str(message)}],
#         "temperature": 0.7
#     }

#     # Convert payload to JSON
#     json_payload = json.dumps(payload)

#     # Send POST request
#     response = requests.post(url, headers=headers, data=json_payload)

#     # Extract content from OpenAI response
#     try:
#         content = response.json()["choices"][0]["message"]["content"]
#     except (KeyError, IndexError) as e:
#         print("Error extracting content from OpenAI response:", e)
#         content = "Failed to extract content from OpenAI response"

#     # Send email using SMTP (MailHog)
#     try:
#         smtp_server = os.getenv('SMTP_SERVER')
#         smtp_port = int(os.getenv('SMTP_PORT'))
#         sender_email = os.getenv('SMTP_FROM_EMAIL')
#         receiver_email = os.getenv('SMTP_TO_EMAIL')

#         msg = MIMEMultipart()
#         msg['From'] = sender_email
#         msg['To'] = receiver_email
#         msg['Subject'] = "Georeport"

#         body = content  # Content from OpenAI response
#         msg.attach(MIMEText(body, 'plain'))

#         with smtplib.SMTP(smtp_server, smtp_port) as server:
#             server.send_message(msg)

#         print("Email sent successfully")
#     except Exception as e:
#         print("Error sending email:", e)

#     # Process the message specifically for Queue 2
#     ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_messages(queue_name, callback):
    """Consume messages from the specified RabbitMQ queue."""
    connection = initialize_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    print(f"Waiting for messages in queue '{queue_name}'")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Interrupted by user, stopping...")
        channel.stop_consuming()
    finally:
        connection.close()

# Define the queues and their corresponding callbacks
queues_callbacks = {
    os.environ.get('RABBITMQ_QUEUE_UPLOADER'): uploader_callback,
    os.environ.get('RABBITMQ_QUEUE_RAW_DATA'): raw_data_callback,
    # Add more queues and callbacks as needed
}

# Start consuming messages from all defined queues in separate threads
threads = []

for queue, callback in queues_callbacks.items():
    if queue:
        thread = threading.Thread(target=consume_messages, args=(queue, callback))
        thread.start()
        threads.append(thread)

# Join threads to ensure all consumers run continuously
for thread in threads:
    thread.join()
