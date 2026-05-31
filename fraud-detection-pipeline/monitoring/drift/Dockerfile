FROM python:3.11-slim

WORKDIR /app

COPY monitoring/drift/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY monitoring/drift/drift_monitor.py /app/drift_monitor.py

CMD ["python", "/app/drift_monitor.py"]
