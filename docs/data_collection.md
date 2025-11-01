# Proceso de Recolección de Datos

Este documento describe el flujo de trabajo para la extracción, parseo y almacenamiento inicial de noticias.

El objetivo de esta fase es recolectar artículos históricos relevantes para "Bitcoin" y guardarlos en archivos JSON crudos, listos para ser ingeridos por el Datalake (MongoDB).

## Scripts Involucrados

* **`collect_data_APIs.py`**: Script principal (orquestador) que ejecuta la recolección.
* **`parser_APIs.py`**: Módulo *helper* que contiene la lógica para normalizar el JSON de la API a nuestro esquema definido (`data_schema.md`).

---

## 1. Fuente de Datos

* **API**: CoinDesk News API
* **Endpoint**: `https://data-api.coindesk.com/news/v1/article/list`
* **Parámetros Clave**:
    * `lang: "EN"` (Inglés)
    * `tag: "bitcoin"`
    * `source_key: "coindesk"`
    * `limit` (artículos por día)
    * `to_ts` (timestamp del día a consultar)

---

## 2. Flujo de Ejecución

El proceso se inicia ejecutando `collect_data_APIs.py`:

1.  **Inicio (`main`):** Se invoca la función `fetch_historical_coindesk()` con los parámetros deseados (ej. `days_back=1500`, `max_total=15000`).

2.  **Iteración Histórica (`fetch_historical_coindesk`):**
    * El script itera día por día hacia atrás, desde "hoy" hasta `days_back` días.
    * Por cada día, llama a `fetch_cryptocompare_day()` para obtener los artículos de esa fecha.

3.  **Extracción y Filtrado (`fetch_cryptocompare_day`):**
    * Se realiza la petición GET al endpoint de CoinDesk.
    * **Lógica de Filtrado (Crítica):** La API (a pesar del tag) puede devolver artículos no relacionados. El script aplica un filtro local estricto:
        * Se unifica el título y el cuerpo del artículo en un solo bloque de texto (`_get_text_blob`).
        * Se extraen las keywords (`_get_keywords`).
        * **Regla:** Un artículo **solo se acepta** si cumple una de estas condiciones:
            1.  Menciona `"bitcoin"` o `"btc"` en sus `keywords`.
            2.  Menciona `"bitcoin"`, `"btc"` o `"satoshi"` (case-insensitive) en el **título o en el cuerpo** (usando la regex `BTC_RE`).
    * Devuelve solo la lista de artículos filtrados.

4.  **Parseo y Normalización (`fetch_historical_coindesk`):**
    * La lista de artículos *crudos filtrados* se pasa a la función `parse_cryptocompare()` (del script `parser_APIs.py`).
    * Esta función transforma el JSON de CoinDesk en el **esquema unificado** (definido en `data_schema.md`), generando el `_id` único con hash MD5.

5.  **Deduplicación:** Se utiliza un `set` (`seen_ids`) para asegurar que solo se añadan artículos únicos a la lista final, basado en el `_id` generado.

6.  **Guardado (`save_json`):**
    * Al finalizar la recolección (o al alcanzar `max_total`), la lista completa de artículos parseados se guarda en un único archivo JSON (ej. `coindesk_historical.json`).
    * Este archivo se almacena en el directorio `/data/raw`.

---

## 3. Paso Siguiente (Ingesta)

Una vez que este script finaliza, el archivo JSON (ej. `coindesk_historical.json`) queda disponible en `/data/raw`.

El script `jsons_to_mongodb.py` es el encargado de leer este (y otros) archivos JSON de ese directorio e insertarlos en la colección de MongoDB, que actúa como nuestro Datalake.