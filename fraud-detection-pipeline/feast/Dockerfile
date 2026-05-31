FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY feast/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY feast/feature_repo /app/feature_repo
COPY feast/scripts /app/scripts

ENV FEAST_REPO=/app/feature_repo
ENV PYTHONPATH=/app/feature_repo

CMD ["python", "/app/scripts/setup_feast.py"]
