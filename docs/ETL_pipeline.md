# Infraestructura y Pipeline ETL (Fase 3)

Este documento describe la arquitectura de contenedores (Docker) y el pipeline de Extracción, Transformación y Carga (ETL) responsable de mover los datos desde los archivos JSON crudos hasta el Data Warehouse (PostgreSQL).

## 1. Visión General de la Arquitectura

El entorno completo está orquestado por `docker-compose.yml` y consiste en tres servicios principales que se ejecutan en una red interna (`backend`):

1.  **`mongo`**: El servicio de base de datos MongoDB. Actúa como **Datalake**, almacenando los artículos recolectados en su formato JSON original (semi-estructurado).
2.  **`postgres`**: El servicio de base de datos PostgreSQL. Actúa como **Data Warehouse (DWH)**, almacenando los datos ya estructurados en una capa "Raw" relacional.
3.  **`etl`**: Un "worker" efímero. Este contenedor construye una imagen de Python, espera a que `mongo` y `postgres` estén listos, y luego ejecuta el pipeline de scripts en secuencia.

[Image of a data pipeline diagram: JSON -> Mongo -> Postgres]

---

## 2. Cómo Ejecutar el Pipeline

1.  Asegurarse de tener un archivo `.env` en la raíz con todas las variables de entorno (usuarios, contraseñas, puertos, etc.) *Revisar .env.example*.
2.  Asegurarse de que los archivos JSON recolectados (ej. `coindesk_historical.json`) estén en la carpeta `./data/raw/`.
3.  Ejecutar el pipeline completo:
    ```bash
    docker-compose up --build
    ```
4.  El servicio `etl` se iniciará automáticamente, esperará a las bases de datos, ejecutará los scripts y luego finalizará. Los servicios `mongo` y `postgres` seguirán corriendo.

---

## 3. Flujo de Ejecución del ETL

El contenedor `etl` es el corazón del pipeline. Su comportamiento está definido por el `Dockerfile` y el `entrypoint.sh`.

1.  **Build (`Dockerfile`)**: Se construye una imagen basada en `python:3.11-slim`. Se instala `netcat-openbsd` (una herramienta de red) y las librerías de `requirements.txt`.
2.  **Start (`docker-compose.yml`)**: El `docker-compose` inicia el contenedor `etl`. Gracias a `depends_on`, se asegura de iniciar `mongo` y `postgres` *antes* de iniciar `etl`.
3.  **Wait (`entrypoint.sh`)**: El `entrypoint.sh` toma el control.
    * Usa `nc` (netcat) para "escuchar" los puertos `postgres:5432` y `mongo:27017`.
    * El script **pausa su ejecución** hasta que ambos puertos estén abiertos, garantizando que las bases de datos estén listas para aceptar conexiones.
4.  **Execute (`entrypoint.sh`)**: Una vez que las bases de datos están listas, el script ejecuta la lógica del ETL en orden:
    * `python scripts/jsons_to_mongodb.py`
    * `python scripts/mongo_to_postgres.py`
    * El contenedor finaliza su ejecución.

---

## 4. Scripts del Pipeline

### Paso 1: `jsons_to_mongodb.py` (Carga al Datalake)

* **Propósito**: Cargar los archivos JSON crudos (de `/data/raw`) en la base de datos MongoDB.
* **Fuente**: Archivos `.json` en el directorio `/app/data/raw` (montado desde el host).
* **Destino**: Colección `raw_articles` (definida por `MONGO_COLLECTION`) en la base de datos `financial_news` (definida por `MONGO_DB`) en MongoDB.
* **Lógica Clave**:
    * Itera sobre todos los archivos `.json` del directorio.
    * Utiliza `collection.insert_many(..., ordered=False)` para una ingesta masiva y eficiente.
    * **Idempotencia**: El script maneja `BulkWriteError`, lo que significa que si se ejecuta de nuevo, los duplicados (basados en el `_id` único) no se reinsertarán y no detendrán el proceso.

### Paso 2: `mongo_to_postgres.py` (Migración a DWH - Raw Layer)

* **Propósito**: Extraer los datos del Datalake (Mongo) y cargarlos en la "Raw Layer" estructurada del Data Warehouse (Postgres).
* **Fuente**: La colección de MongoDB poblada en el paso anterior.
* **Destino**: La tabla `articles` en la base de datos PostgreSQL.
* **Lógica Clave**:
    1.  **DDL (Data Definition Language)**: Ejecuta `CREATE TABLE IF NOT EXISTS articles (...)`. Esto crea la tabla la primera vez y no falla en ejecuciones subsecuentes.
    2.  **Mapeo de Datos**: Itera sobre cada documento (`doc`) en la colección de Mongo.
    3.  **Transformación Leve**:
        * Convierte el `_id` de Mongo a `str` para usarlo como `id` (PRIMARY KEY) en Postgres.
        * Utiliza una función `parse_datetime` para manejar correctamente los timestamps.
        * Mapea el campo anidado `extra` de Mongo a una columna `JSONB` en Postgres.
    4.  **Carga e Idempotencia**:
        * Inserta cada fila usando `INSERT INTO articles ...`.
        * Utiliza `ON CONFLICT (id) DO NOTHING`. Esto es crucial: si un artículo con el mismo `id` ya existe en Postgres, simplemente se omite. El pipeline puede ejecutarse múltiples veces sin crear duplicados.

---

## 5. Esquema DWH - Raw Layer (PostgreSQL)

El script `mongo_to_postgres.py` define y crea la siguiente tabla en PostgreSQL, que sirve como la primera capa estructurada de nuestro Data Warehouse.

| Columna | Tipo | Descripción |
| :--- | :--- | :--- |
| **`id`** | `TEXT` | Llave primaria. Es el `_id` (hash MD5) importado de MongoDB. |
| **`title`** | `TEXT` | Titular del artículo. |
| **`description`** | `TEXT` | Descripción o subtítulo. |
| **`content`** | `TEXT` | Cuerpo o texto completo del artículo. |
| **`url`** | `TEXT` | URL al artículo original. |
| **`source`** | `TEXT` | Nombre de la fuente (ej. "coindesk"). |
| **`published_at`** | `TIMESTAMP` | Fecha de publicación original. |
| **`collected_at`** | `TIMESTAMP` | Fecha de recolección (por nuestro script). |
| **`extra`** | `JSONB` | Contenedor para todos los metadatos extra (keywords, lang, score, etc.). |