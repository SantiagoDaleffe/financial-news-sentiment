#!/bin/sh
set -e

echo "Esperando a Postgres..."
until nc -z postgres 5432; do
  sleep 1
done

echo "Esperando a Mongo..."
until nc -z mongo 27017; do
  sleep 1
done

echo "Insertando jsons en Mongo..."
python scripts/jsons_to_mongodb.py

echo "Migrando Mongo a Postgres..."
python scripts/mongo_to_postgres.py

echo "ETL completado"