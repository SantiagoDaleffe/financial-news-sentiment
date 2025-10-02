import os
import json
from datetime import datetime
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
mongo_client = MongoClient(mongo_uri)
collection = mongo_client[MONGO_DB][MONGO_COLLECTION]

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT"))
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

pg_conn = psycopg2.connect(
	host=POSTGRES_HOST,
	port=POSTGRES_PORT,
	user=POSTGRES_USER,
	password=POSTGRES_PASSWORD,
	dbname=POSTGRES_DB,
)
pg_cursor = pg_conn.cursor()

pg_cursor.execute("""
CREATE TABLE IF NOT EXISTS articles (
	id TEXT PRIMARY KEY,
	title TEXT,
	description TEXT,
	content TEXT,
	url TEXT,
	source TEXT,
	published_at TIMESTAMP,
	collected_at TIMESTAMP,
	extra JSONB
);
""")
pg_conn.commit()

def parse_datetime(value):
	if not value:
		return None
	if isinstance(value, datetime):
		return value
	try:
		return datetime.fromisoformat(value.replace("Z", ""))
	except Exception:
		return None

for doc in collection.find():
	pg_cursor.execute("""
	INSERT INTO articles (id, title, description, content, url, source, published_at, collected_at, extra)
	VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
	ON CONFLICT (id) DO NOTHING;
	""", (
		str(doc.get("_id")),
		doc.get("title"),
		doc.get("description"),
		doc.get("content"),
		doc.get("url"),
		doc.get("source"),
		parse_datetime(doc.get("published_at")),
		parse_datetime(doc.get("collected_at")),
		Json(doc.get("extra", {})),
	))
	pg_conn.commit()

pg_cursor.close()
pg_conn.close()
mongo_client.close()

print("Exportación completada con éxito")