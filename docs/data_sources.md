# Data Sources Documentation

Este documento describe las fuentes de datos utilizadas en el proyecto, incluyendo detalles de acceso, estructura de la respuesta y ejemplos de uso.

---

## 1. Collector (coindesk).

**Descripción:**  
Coindesk ofrece un feed de noticias financieras y de criptomonedas a través de su API pública. Se utiliza principalmente para recolectar artículos relacionados con Bitcoin y temas asociados. No presenta límites de uso estrictos en la práctica, por lo que resulta adecuada para recolección en cantidad.

**Endpoint principal:**  
https://data-api.coindesk.com/news/v1/article/list

**Parámetros principales:**  
- `search_string`: palabra clave de búsqueda (ej: `"BTC"`).  
- `lang`: idioma (ej: `"EN"`).  
- `limit`: cantidad máxima de artículos por request (ej: `8`).  
- `to_ts`: límite superior en formato timestamp UNIX (ej: fin de un día específico).  
- `source_key`: fuente de origen (ej: `"coindesk"`, `"cointelegraph"`).  

**Ejemplo de respuesta recortado**
```json
{
  "Message": "News list successfully returned",
  "Data": [
    {
      "ID": "123456",
      "TITLE": "Bitcoin Hits New All-Time High",
      "SUBTITLE": "BTC price surges past $100,000",
      "BODY": "Bitcoin reached unprecedented levels today as...",
      "URL": "https://www.coindesk.com/bitcoin-hits-high",
      "IMAGE_URL": "https://images.coindesk.com/article.png",
      "KEYWORDS": "Bitcoin,BTC,Markets",
      "LANG": "EN",
      "PUBLISHED_ON": 1756353310,
      "SOURCE_ID": "coindesk",
      "SOURCE_DATA": { "NAME": "Coindesk" },
      "SCORE": 0.98
    }
  ]
}

**Notas:**  
- La clave principal es `"Data"`, que contiene la lista de artículos.  
- `"PUBLISHED_ON"` está en timestamp UNIX.  
- `"SOURCE_DATA.NAME"` indica la fuente real (Coindesk, Cointelegraph, etc.).
- Algunos campos pueden venir vacíos (`"SUBTITLE"`, `"IMAGE_URL"`, etc.).

## 2. Parser.
**Descripción:**
El parser normaliza los artículos obtenidos de la API en un formato estándar, generando un id único y enriqueciendo con metadatos.

**Transformaciones principales:**
