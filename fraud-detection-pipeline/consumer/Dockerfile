FROM python:3.11-slim

WORKDIR /app

COPY consumer/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY consumer/consumer.py /app/consumer.py

CMD ["python", "/app/consumer.py"]
