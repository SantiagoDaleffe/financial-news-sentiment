# Esquema de Datos - Datalake (MongoDB)

Este documento define el esquema de los documentos almacenados en la colección de MongoDB (`raw_articles`), que actúa como el Datalake para los artículos recolectados.

El esquema es generado principalmente por el script `parser_APIs.py` y garantiza una estructura normalizada para los datos crudos JSON provenientes de diversas fuentes.

---

## Esquema Principal

La estructura base de cada documento en la colección.

| Campo | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| **`_id`** | `string` | Hash MD5 único generado a partir de `source::title::url`. Actúa como clave primaria. | `"b1a...f93"` |
| **`title`** | `string` | Titular del artículo. Valor por defecto: `"Untitled"`. | `"Bitcoin rises above $65k"` |
| **`description`** | `string` | Breve descripción o subtítulo. Valor por defecto: `""` (string vacío). | `"BTC reached new highs..."` |
| **`content`** | `string` | Texto completo del artículo. Valor por defecto: `""` (string vacío). | `"Bitcoin price surged today..."` |
| **`url`** | `string` | Enlace URL al artículo original. | `"https://www.coindesk.com/..."` |
| **`source`** | `string` | Nombre de la fuente (ej. "CoinDesk", "CryptoCompare"). | `"coindesk"` |
| **`published_at`** | `datetime` | Fecha de publicación original del artículo (convertida a objeto `datetime`). | `ISODate("2025-08-25T14:32:00Z")` |
| **`collected_at`** | `datetime` | Fecha y hora en que se recopiló el dato (generado por `datetime.now()`). | `ISODate("2025-08-25T18:45:00Z")` |
| **`extra`** | `dict` | Objeto anidado con metadatos adicionales específicos de la fuente. | `{ "lang": "EN", "keywords": [...] }` |

---

## Esquema Anidado: `extra`

El campo `extra` contiene metadatos que no son universales en todas las fuentes, pero que se extraen durante el parseo.

| Campo (dentro de `extra`) | Tipo | Descripción |
| :--- | :--- | :--- |
| **`lang`** | `string` | Código de idioma del artículo (ej. "EN", "es"). Valor por defecto: `"unknown"`. |
| **`keywords`** | `list[string]` | Lista de palabras clave o tags asociados al artículo. |
| **`image`** | `string` | URL de la imagen principal del artículo. |
| **`source_id`** | `any` | Identificador interno de la fuente (si lo provee la API). |
| **`score`** | `any` | Puntuación o ranking de relevancia (si lo provee la API). |

---

## Notas

* Este esquema representa la capa "Raw" (Datalake) del proyecto.
* El script `jsons_to_mongodb.py` carga los archivos JSON (que siguen este esquema) en la base de datos, manejando duplicados gracias al `_id` único (genera un `BulkWriteError` por duplicados, pero los inserta si no existen).
* Los campos de texto (`title`, `description`, `content`) tienen un valor por defecto (string vacío o "Untitled") para evitar valores nulos (`null`).