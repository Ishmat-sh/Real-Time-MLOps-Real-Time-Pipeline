FROM python:3.11-slim

WORKDIR /app

COPY training/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY training/train.py /app/train.py

ENV DATA_DIR=/app/data
ENV MODEL_DIR=/app/output/models

CMD ["python", "/app/train.py"]
