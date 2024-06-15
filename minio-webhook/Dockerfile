FROM python:3.10.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port FastAPI runs on
EXPOSE 5001

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001"]
