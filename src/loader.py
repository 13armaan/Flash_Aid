import sys, os, re, time, requests, sqlalchemy as sa  # type: ignore
from requests.adapters import HTTPAdapter, Retry  # type: ignore
from bs4 import BeautifulSoup
from dotenv import load_dotenv  # type: ignore
from urllib.parse import urlparse
from tqdm import tqdm  # type: ignore
import traceback
import random

load_dotenv()
ENGINE = sa.create_engine(os.environ["TIDB_DATABASE_URL"], pool_recycle=300)

def clean_text(html):
   
    html = re.sub(r"<(script|style|noscript)[\s\S]*?</\1>", "", html, flags=re.I)
    soup = BeautifulSoup(html, "lxml")  # faster parser
    for s in soup(["script", "style", "noscript"]):
        s.extract()
    text = soup.get_text("\n")
    text = re.sub(r"\n{2,}", "\n", text).strip()
    return text

def chunk_text(text, target_chars=1000, overlap=200):
    chunks, i = [], 0
    while i < len(text):
        yield text[i:i+target_chars]
        i+=target_chars-overlap

def insert_doc(cx, src, lang, url, title, license):
    res = cx.exec_driver_sql(
        "INSERT INTO documents(source,lang,url,title,license) VALUES (%s,%s,%s,%s,%s)",
        (src, lang, url, title, license),
    )
    return res.lastrowid

def insert_chunk(cx, doc_id, seq, text):
    res = cx.exec_driver_sql(
        "INSERT INTO chunks(doc_id,seq,text) VALUES (%s,%s,%s)",
        (doc_id, seq, text),
    )
    return res.lastrowid

def guess_source(url):
    host = urlparse(url).netloc
    if "who.int" in host:
        return "WHO"
    if "nhs.uk" in host:
        return "NHS"
    if "cdc.gov" in host:
        return "CDC"
    if "data.gov.in" in host:
        return "OGD"
    return host

def guess_license(url):
    if "who.int" in url:
        return "CC BY-NC-SA 3.0 IGO"
    if "nhs.uk" in url:
        return "Open Government Licence v3.0 (UK)"
    if "cdc.gov" in url:
        return "Public Domain (US Federal)"
    if "data.gov.in" in url:
        return "Government Open Data License - India (GODL-India)"
    return "Unknown"

session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "HEAD"],
)
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))

def main(path):
    with open(path) as f:
        urls = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]

    with ENGINE.begin() as cx:
        for url in tqdm(urls, desc="loading"):
            try:
                r = session.get(url, timeout=30, stream=True)
                r.raise_for_status()

                if (
                    "application/pdf" in r.headers.get("Content-Type", "")
                    or url.lower().endswith(".pdf")
                ):
                    print(f"skip PDF {url}")
                    continue

              
                size_limit = 2_000_000
                html_parts = []
                downloaded = 0
                for chunk in r.iter_content(8192, decode_unicode=True):
                    if not chunk:
                        continue
                    html_parts.append(chunk)
                    downloaded += len(chunk)
                    if downloaded > size_limit:
                        print(f"Truncated large page: {url}")
                        break
                html = "".join(html_parts)

            
                title_match = re.search(
                    r"<title>(.*?)</title>", html, re.I | re.S
                )
                title = title_match.group(1).strip() if title_match else ""

               
                text = clean_text(html)
                doc_id = insert_doc(
                    cx, guess_source(url), "en", url, title, guess_license(url)
                )
                for i, ch in enumerate(chunk_text(text)):
                    insert_chunk(cx, doc_id, i, ch)

                time.sleep(random.uniform(1, 3))

            except Exception as e:
                print("ERR", url, e)
                print(f"    TYPE: {type(e).__name__}")
                print(f"    DETAIL: {e}")
                traceback.print_exc()
            time.sleep(random.uniform(2, 5))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/loader.py data/seed_urls.txt")
        sys.exit(1)
    main(sys.argv[1])
