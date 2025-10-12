FROM python:3.11-slim
WORKDIR /app
COPY app/ /app/
COPY requirements.txt .
COPY .env .
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
