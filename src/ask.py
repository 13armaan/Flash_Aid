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
        if rows: return rows

        rows=cx.exec_driver_sql(
            """            
            SELECT c.text,d.title,d.url,d.source
            FROM chunks c JOIN documents d ON d.id=c.doc_id
            WHERE c.text LIKE %s LIMIT %s 
            """,
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
    return instructions +"\n\nContext:\n" + "\n\n".join(ctx) + f"\n\nQuestions:{q}\n"

def call_llm(prompt: str, model: str = "kimi-k2-0711-preview") -> str:
    try:
        api_key = os.getenv("MOONSHOT_API_KEY")
      
        if not api_key:
            return "(Moonshot LLM error) Missing API key. Set MOONSHOT_API_KEY."

        base_url = os.getenv("MOONSHOT_BASE_URI", "https://api.moonshot.ai/v1")
        endpoint = f"{base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "user",
                 "content": prompt
                 },
                
                 ]
        }

        resp = requests.post(endpoint, json=payload, headers=headers, timeout=30)
      
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("LLM ERROR OCCURED")
        print("Error:",e)
        traceback.print_exc()
        return f"(MOONSHOT LLM ERROR) {e}\n\nPrompt:\n{prompt[:1200]}"    
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



