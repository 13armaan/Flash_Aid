import sys,os,re,time, requests,sqlalchemy as sa # type: ignore
from bs4 import BeautifulSoup
from dotenv import load_dotenv # type: ignore
from urllib.parse import urlparse
from tqdm import tqdm # type: ignore

load_dotenv()
ENGINE =sa.create_engine(os.environ["TIDB_DATABASE_URL"], pool_recycle=300)

def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for s in soup(["script","style","noscript"]): s.extract()
    text= soup.get_text("\n")
    text=re.sub(r'\n{2,}','\n',text).strip()
    return text

def chunk_text(text, target_chars=3500, overlap=500):
    chunks, i=[], 0
    while i<len(text):
        j=min(i+target_chars,len(text))
        k=text.rfind("\n",i+int(target_chars*0.8),j)
        if k==-1 : k=j
        chunks.append(text[i:k].strip())
        i=k-overlap
        if i<0:i=0
        if k==j : i=j-overlap
        if i<0: i=0
        if i>=len(text): break
    
    return[c for c in chunks if c]

def insert_doc(cx,src,lang,url,title,license):
    res=cx.exec_driver_sql(
        "INSERT INTO documents(source,lang,url,title,license) VALUES (%s,%s,%s,%s,%s)",
        (src,lang,url,title,license)
    ) 
    return res.lastrowid

def insert_chunk(cx,doc_id,seq,text):
    res=cx.exec_driver_sql(
        "INSERT INTO chunks(doc_id,seq,text) VALUES (%s,%s,%s)",
        (doc_id,seq,text)
    )
    return res.lastrowid

def guess_source(url):
    host=urlparse(url).netloc
    if "who.int" in host: return "WHO"
    if "nhs.uk" in host : return "NHS"
    if "cdc.gov" in host: return "CDC"
    if "data.gov.in" in host : return "OGD"
    return host

def guess_license(url):
    if "who.int" in url: return "CC BY-NC-SA 3.0 IGO"
    if "nhs.uk" in url : return "Open Government Licence v3.0 (UK)"
    if "cdc.gov" in url: return "Public Domain (US Federal)"
    if "data.gov.in" in url : return "Government Open Data License - India (GODL-India)"
    return "Unknown"

def main(path):
    with open(path) as f: urls =[l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    with ENGINE.begin() as cx:
        for url in tqdm(urls, desc="loading"):
            try:
                r=requests.get(url,timeout=30)
                r.raise_for_status()
                text=clean_text(r.text)
                title = (re.search(r"<title>(.*?)</title>", r.text,re.I | re.S) or ["",""])[1].strip()
                doc_id=insert_doc(cx,guess_source(url),"en",url,title,guess_license(url))
                for i,ch in enumerate(chunk_text(text)):
                    insert_chunk(cx,doc_id,i,ch)
                
                time.sleep(1)

            
            except Exception as e:
                print("ERR",url,e)

if __name__ =="__main__":
    if len(sys.argv) <2:
        print("Usage: python src/loader.py data/seed_urls.txt"); sys.exit(1)
    main(sys.argv[1])
    