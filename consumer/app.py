import os
import pika
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    print(message)
    # Process the message specifically for Queue 1
    # ...
    ch.basic_ack(delivery_tag=method.delivery_tag)

# def callback_for_queue2(ch, method, properties, body):
#     print("Received message from Queue 2:")
#     message = json.loads(body)
#     print(message)
#     # Process the message specifically for Queue 2
#     # ...
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
    "uploader": uploader_callback,
    # os.environ.get('RABBITMQ_QUEUE2'): callback_for_queue2,
    # Add more queues and callbacks as needed
}

# Start consuming messages from all defined queues
for queue, callback in queues_callbacks.items():
    if queue:
        consume_messages(queue, callback)
