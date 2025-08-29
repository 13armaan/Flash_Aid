import os,sys,sqlalchemy as sa 
from sqlalchemy import text as sql
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np
from rich.console import Console
from rich.markdown import Markdown
from safety import is_dangerous, disclaimer
import requests
import traceback
console=Console()
load_dotenv()
TOP_K=int(os.getenv("TOP_K","5"))
engine=sa.create_engine(os.environ["TIDB_DATABASE_URL"],pool_recycle =300)
emb=SentenceTransformer("all-MiniLM-L6-v2")

def vec_literal(q):
    v=emb.encode([q],convert_to_numpy=True,normalize_embeddings=True)[0]
    return "["+",".join(f"{x:.6f}" for x in v.tolist())+"]"

def retrieve(q):
    qv=vec_literal(q)
    with engine.begin() as cx:
        rows=cx.exec_driver_sql(
            """            SELECT c.text, d.title, d.url, d.source
            FROM embeddings e JOIN chunks c ON e.chunk_id=c.id JOIN documents d ON d.id=c.doc_id
            ORDER BY VEC_COSINE_DISTANCE(e.vec,%s) LIMIT %s """ ,
            (qv,TOP_K)
        ).fetchall()
        cites=[]
        for i,(text,title,url,src) in enumerate(rows,start=1):
            cites.append(f"[{i}] {title} - {url}")
        if rows: return [{
            "text":r[0],
            "title":r[1],
            "url":r[2],
            "source":r[3]    
        }
        for r in rows
        ],cites

        rows=cx.exec_driver_sql(
            """            
            SELECT c.text,d.title,d.url,d.source
            FROM chunks c JOIN documents d ON d.id=c.doc_id
            WHERE c.text LIKE %s LIMIT %s 
            """,
            (f"%{q.split()[0]}%",TOP_K)
        ).fetchall()
        
        return [{
            "text":r[0],
            "title":r[1],
            "url":r[2],
            "source":r[3],   
        }
        for r in rows
        ],cites
if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage:python src/tools/search_docs.py \"your query\"")
        sys.exit(1)
    q=sys.argv[1]
    results=search_docs(q)
    for i,r in enumerate(results,1):
      print(f"[{i}] {r['title']} ({r['source']}) - {r['url']}\n{r['text'][:200]}...\n")

#This is now both executable from cli and can also be imported