import os
import json
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

MONGO_USER = os.getenv("MONGO_USER", "Poggerv2")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "lr64370l9cv7")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_DB = os.getenv("MONGO_DB", "financial_news")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "articles")
DATA_DIR = "/app/data/raw"

def load_json_files_to_mongo():
	client = MongoClient(
		f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/",
		authSource="admin"
	)
	db = client[MONGO_DB]
	collection = db[MONGO_COLLECTION]
	print(f"🔍 Conectado a MongoDB en {MONGO_HOST}:{MONGO_PORT}, db={MONGO_DB}, collection={MONGO_COLLECTION}")

	for filename in os.listdir(DATA_DIR):
		if filename.endswith(".json"):
			filepath = os.path.join(DATA_DIR, filename)
			print(f"Procesando {filepath}...")
			with open(filepath, "r", encoding="utf-8") as f:
				try:
					data = json.load(f)
					if isinstance(data, dict):
						data = [data]
				except json.JSONDecodeError as e:
					print(f"Error leyendo {filename}: {e}")
					continue

				if data:
					try:
						result = collection.insert_many(data, ordered=False)
						print(f"✅ Insertados {len(result.inserted_ids)} documentos desde {filename}")
					except BulkWriteError as bwe:
						inserted_count = bwe.details.get("nInserted", 0)
						dup_count = len(data) - inserted_count
						print(f"{filename}: {inserted_count} insertados, {dup_count} duplicados.")

	total_docs = collection.count_documents({})
	print(f"Total de documentos en la colección: {total_docs}")

if __name__ == "__main__":
	load_json_files_to_mongo()