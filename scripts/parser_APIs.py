import hashlib
from datetime import datetime


def generate_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def parse_cryptocompare(article: dict) -> dict:
    title = (article.get("TITLE") or article.get("title") or "Untitled")
    content = (article.get("BODY") or article.get("CONTENT") or article.get("content") or "")
    keywords = (article.get("KEYWORDS") or article.get("keywords") or "")

    source_name = (article.get("SOURCE_DATA", {}) .get("NAME")
                   or article.get("source")
                   or article.get("Source")
                   or "")
    unique_str = f"{source_name}::{title}::{article.get('URL') or ''}"

    _id = generate_id(unique_str)

    return {
        "_id": _id,
        "title": title,
        "description": article.get("SUBTITLE") or article.get("description") or "",
        "content": content,
        "url": article.get("URL") or article.get("url"),
        "source": source_name,
        "published_at": (
            datetime.fromtimestamp(article["PUBLISHED_ON"])
            if article.get("PUBLISHED_ON") else article.get("published_at")
        ),
        "collected_at": datetime.now(),
        "extra": {
            "lang": article.get("LANG") or article.get("lang") or "unknown",
            "keywords": (keywords.split(",") if isinstance(keywords, str) and keywords else (keywords if isinstance(keywords, list) else [])),
            "image": article.get("IMAGE_URL") or article.get("image") or "",
            "source_id": article.get("SOURCE_ID"),
            "score": article.get("SCORE"),
        },
    }
