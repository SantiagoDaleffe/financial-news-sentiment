import json
import time
import requests
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from parser_APIs import parse_cryptocompare

# paths
data_path = Path(__file__).resolve().parents[1] / "data" / "raw"
data_path.mkdir(parents=True, exist_ok=True)

BTC_RE = re.compile(r"\b(bitcoin|btc|satoshi)\b", flags=re.IGNORECASE)

def _get_source_name(item):
    return (item.get("SOURCE_DATA", {}).get("NAME")
            or item.get("source")
            or item.get("Source")
            or item.get("source_name")
            or "").strip().lower()

def _get_keywords(item):
    for k in ("KEYWORDS", "keywords", "TAGS", "tags"):
        val = item.get(k)
        if not val:
            continue
        if isinstance(val, str):
            return [t.strip().lower() for t in val.split(",") if t.strip()]
        if isinstance(val, list):
            return [str(t).strip().lower() for t in val]
    return []

def _get_text_blob(item):
    title = (item.get("TITLE") or item.get("title") or "").strip().lower()
    body = (item.get("BODY") or item.get("CONTENT") or item.get("content") or "").strip().lower()
    return f"{title} {body}"

def fetch_cryptocompare_day(date=None, per_day=10):
    if date is None:
        date = datetime.utcnow()
    to_ts = int(datetime(date.year, date.month, date.day, 23, 59, 59).timestamp())

    url = "https://data-api.coindesk.com/news/v1/article/list"
    params = {"lang": "EN", "limit": per_day, "to_ts": to_ts, "tag": "bitcoin", "source_key": "coindesk"}
    headers = {"Content-type": "application/json; charset=UTF-8"}

    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json().get("Data", []) or []

    logging.info(f"[fetch_cryptocompare_day] raw total={len(data)}")

    filtered = []
    for it in data:
        text_blob = _get_text_blob(it)
        keywords = _get_keywords(it)
        
        # Aceptamos cualquier artículo de la API de Coindesk
        # que mencione BTC en title/body o en keywords
        if any("bitcoin" in k or "btc" in k for k in keywords) or BTC_RE.search(text_blob):
            filtered.append(it)


    logging.info(f"[fetch_cryptocompare_day] filtered={len(filtered)}")
    return filtered

def fetch_historical_coindesk(days_back=60, per_day=10, max_total=1000):
    all_articles = []
    seen_ids = set()
    today = datetime.utcnow()
    for i in range(days_back):
        day = today - timedelta(days=i)
        try:
            raw = fetch_cryptocompare_day(date=day, per_day=per_day)
            parsed = [parse_cryptocompare(a) for a in raw]

            for p in parsed:
                if p["_id"] not in seen_ids:
                    all_articles.append(p)
                    seen_ids.add(p["_id"])

            logging.info(f"{day.date()} → {len(parsed)} artículos procesados (total {len(all_articles)})")
        except Exception as e:
            logging.error(f"Error {day.date()}: {e}")
        if len(all_articles) >= max_total:
            break
        time.sleep(0.1)
    return all_articles

def save_json(data, fname="coindesk_historical.json"):
    file_path = data_path / fname
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str, indent=2)
    logging.info(f"Saved {len(data)} artículos en {file_path}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    articles = fetch_historical_coindesk(days_back=1500, per_day=10, max_total=15000)
    if articles:
        save_json(articles)
        logging.info(f"Total final: {len(articles)} artículos")
    else:
        logging.warning("No se encontraron artículos.")

if __name__ == "__main__":
    main()
