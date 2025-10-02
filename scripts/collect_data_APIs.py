# config
import os
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from parser_APIs import parse_cryptocompare
import logging

articles = []

# paths
data_path = Path(__file__).resolve().parents[1] / "data" / "raw"
data_path.mkdir(parents=True, exist_ok=True)


def fetch_cryptocompare_day(query="BTC", source="coindesk", date=None, per_day=2):
    if date is None:
        date = datetime.utcnow()
    end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)
    to_ts = int(end_of_day.timestamp())

    url = "https://data-api.coindesk.com/news/v1/article/list"
    params = {
        "search_string": query,
        "lang": "EN",
        "limit": per_day,
        "to_ts": to_ts,
        "source_key": source,
    }
    headers = {"Content-type": "application/json; charset=UTF-8"}
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()["Data"]


def fetch_historical_crypto(query="BTC", source="coindesk", days_back=60, per_day=2, max_total=100):
    all_articles = []
    seen_ids = set()
    today = datetime.utcnow()

    for i in range(days_back):
        day = today - timedelta(days=i)
        try:
            raw = fetch_cryptocompare_day(query=query, source=source, date=day, per_day=per_day)
            parsed = [parse_cryptocompare(a) for a in raw]

            unique = [p for p in parsed if p["_id"] not in seen_ids]
            for p in unique:
                seen_ids.add(p["_id"])

            
            all_articles.extend(unique)
            print(f"{day.date()} → {len(unique)} nuevos artículos (total {len(all_articles)})")

        except Exception as e:
            print(f"Error {day.date()}: {e}")

        if len(all_articles) >= max_total:
            break
        time.sleep(0.1)

    return all_articles

# saves 
def save_json(data, source):
    file_path = data_path / f"{source}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str, indent=2)
    print(f"Saved {len(data)} articles in {file_path}")


# main
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    all_articles = []
    seen_ids = set()

    try:
        parsed_coindesk = fetch_historical_crypto(
            query="BTC", source="coindesk", days_back=1000, per_day=8, max_total=8000
        )

        if parsed_coindesk:
            save_json(parsed_coindesk, "coindesk_historical")
            logging.info(f"Coindesk: {len(parsed_coindesk)} artículos")
            all_articles.extend(parsed_coindesk)
        else:
            logging.warning("No articles found in Coindesk.")

    except Exception as e:
        logging.error(f"Error fetching from Coindesk: {e}")

    try:
        parsed_cointelegraph = fetch_historical_crypto(
            query="BTC", source="cointelegraph", days_back=1000, per_day=5, max_total=5000
        )

        if parsed_cointelegraph:
            save_json(parsed_cointelegraph, "cointelegraph_historical")
            logging.info(f"Cointelegraph: {len(parsed_cointelegraph)} artículos")
            all_articles.extend(parsed_cointelegraph)
        else:
            logging.warning("No articles found in Cointelegraph.")

    except Exception as e:
        logging.error(f"Error fetching from Cointelegraph: {e}")

    deduped = []
    for art in all_articles:
        if art["_id"] not in seen_ids:
            seen_ids.add(art["_id"])
            deduped.append(art)

    save_json(deduped, "merged_news")
    logging.info(f"Total merged (deduped): {len(deduped)} artículos")

if __name__ == "__main__":
    main()