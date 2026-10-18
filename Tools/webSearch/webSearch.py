from html import unescape as _unescape
import hashlib
import re
import urllib.parse
import urllib.request
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "websearch"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"


def search(query: str, limit: int = 10) -> list[dict]:
    from ddgs import DDGS

    results: list[dict] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=limit):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "body": r.get("body", ""),
            })
    return results


def extract(url: str, max_chars: int = 5000) -> str:
    cache_key = hashlib.md5(url.encode()).hexdigest()[:12]
    cache_file = CACHE_DIR / f"{cache_key}.txt"

    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        html = (
            urllib.request.urlopen(req, timeout=15)
            .read()
            .decode("utf-8", errors="replace")
        )
    except Exception as e:
        return f"[ERROR] {e}"

    body = html
    for tag in [
        "article", "main", 'div[class*="content"]',
        'div[class*="post"]', "body",
    ]:
        tag_name = tag.split("[", 1)[0]
        m = re.search(
            f"<{tag}[^>]*>(.*?)</{tag_name}>",
            html, re.DOTALL | re.IGNORECASE,
        )
        if m:
            body = m.group(1)
            break

    text = re.sub(
        r"<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>",
        "", body, flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text[:max_chars]

    cache_file.write_text(text, encoding="utf-8")
    return text


def webSearch(
    query: str, limit: int = 1, max_per_page: int = 3000, write=print
) -> list[dict]:
    write(f'Searching for "{query}"...')
    results = search(query, limit)
    for r in results:
        r["content"] = extract(r["url"], max_per_page)
    return results
