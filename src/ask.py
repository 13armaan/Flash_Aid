import os,sys,sqlalchemy as sa 
from sqlalchemy import text as sql
from dotenv import load_dotenv
from sentence_transformwers import SentenceTransformer
import numpy as np
from rich.console import Console
from rich.markdown import Markdown
from safety import is_dangerous, disclaimer

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
            """
            SELECT c.text, d.title, d.url, d.soutrce
            FROM embeddings e JOIN chunks c ON e.chunk_id=c.id JOIN documents on d ON d.id=doc_id
            ORDER BY VEC_COSINE_DISTANCE(e.vec,%s) LIMIT %s,
            """ 
            (qv,TOP_K)
        ).fetchall()
        if rows: return rows

        roes=cx.exec_driver_sql(
            """
            SELECT c.text,d.title,d.url,d.source
            FROM chunks c JOIN documents d ON d.id=c.doc_id
            WHERE c.text LIKE %s LIMIT %s
            """
            (f"%{q.split()[0]}%",TOP_K)
        ).fetchall()
        return rows
    
def build_prompt(q,rows):
    cites=[]
    ctx=[]
    for i,(text,title,url,src) in enumerate(rows,start=1):
        cites.append(f"[{i}] {title} - {url}")
        ctx.append(f"(Source {i}: {src}) {text[:1000]}")
    instructions=(
        """
        You are a cautious health assistant. Answer clearly in bullet points
        Cite sources inline like[1], [2]. Add first-aid steps when relevant
        Explicity say this is not medical advice
        """
    )
    return instructions +"\n\nCotext:\n" + "\n\n" .join(ctx) + f"\n\Questions:{q}\n"
def call_llm(prompt):
    try:
        import ollama,os
        host =os.getenv("OLLAMA_HOSt","http://127.0.0.1:11434")
        client =ollama.Client(host=host)
        res=client.chat(model="llama3.1:8b", messages=[{"role":"user","content":prompt}])
        return res["message"]["content"].strip()
    except Exception as e:
        return f"(LLM unavailable) {e}\n\nHere are the most relevant sources:\n"+ prompt[:1200]
    
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 src/ask.py \"Your health question\"")
        sys.exit(1)
    q=sys.argv[1]
    if is_dangerous(q):
        console.print(Markdown("**"+disclaimer()+"**"))
        sys.exit(0)
    rows=retrieve(q)
    if not rows:
        console.print("No results yet. Try loading data (make load) and embedding (make ambed).")
        sys.exit(1)
    prompt=build_prompt(q,rows)
    answer=call_llm(prompt)
    console.rule("[bold]Answer")
    console.print(Markdown(answer+"\n\n**"+disclaimer()+"**"))
    console.rule("[bold]Sources")
    for i,(_,title,url,src) in enumerate(rows,start=1):
        console.print(f"[{i}] {title} ({src}) - ({url})")

if __name__=="__main__":
    main()



