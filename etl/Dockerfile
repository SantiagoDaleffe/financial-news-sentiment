FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY etl/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY scripts ./scripts
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]