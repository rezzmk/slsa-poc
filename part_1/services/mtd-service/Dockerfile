FROM python:3.9-slim

WORKDIR /app

# Install Docker SDK dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

CMD ["python", "app.py"]
