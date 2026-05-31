FROM python:3.11-slim

WORKDIR /app

COPY producer/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY producer/producer.py /app/producer.py

CMD ["python", "/app/producer.py"]
