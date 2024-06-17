import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

app = FastAPI()

# Load environment variables
load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

@app.post('/init')
async def init():
    return JSONResponse(content={"status": "initialized"})

@app.post('/run')
async def run(request: Request):
    try:
        
        event = await request.json()
        # API endpoint
        url = "https://api.openai.com/v1/chat/completions"

        # Request headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        # Request payload
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "can you give me a description of the below raster data? what does this mean for this .tiff file?" + str(event)}],
            "temperature": 0.7
        }

        # Convert payload to JSON
        json_payload = json.dumps(payload)

        # Send POST request
        response = requests.post(url, headers=headers, data=json_payload)

        # Extract content from OpenAI response
        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            print("Error extracting content from OpenAI response:", e)
            content = "Failed to extract content from OpenAI response"

        # Send email using SMTP (MailHog)
        try:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT'))
            sender_email = os.getenv('SMTP_FROM_EMAIL')
            receiver_email = os.getenv('SMTP_TO_EMAIL')

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = "Georeport"

            body = content  # Content from OpenAI response
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.send_message(msg)           
            
        except Exception as e:
            return JSONResponse(content={"status": "error", "message": "Error sending email"})
        
        return JSONResponse(content={"status": "success", "message": "Report generated successfully"})    
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return JSONResponse(content={"status": "error", "message": f"An unexpected error occurred: {e}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)