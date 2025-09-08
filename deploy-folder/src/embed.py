import os,numpy as np,sqlalchemy as sa
from sqlalchemy import text as sql
from dotenv import load_dotenv
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

load_dotenv()
engine=sa.create_engine(os.environ["TIDB_DATABASE_URL"], pool_recycle=300)
model = SentenceTransformer("all-MiniLM-L6-v2")

def vec_to_text(v):
    return "["+",".join(f"{x:.6f}" for x in v.tolist())+"]"
def fetch_chunks(batch_size=100):
 while True:
  with engine.begin() as cx:
    rows=cx.exec_driver_sql(
        f"""
        SELECT c.id, c.text
        FROM chunks c
        LEFT JOIN embeddings e ON e.chunk_id=c.id
        WHERE e.chunk_id IS NULL
        ORDER by c.id
        LIMIT {batch_size}
        """
        ).fetchall()
    if not rows:
       break
    yield rows
for rows in fetch_chunks(batch_size=500):
 texts=[r[1] for r in rows]
 ids =[r[0] for r in rows]

 batch_size=1
 chunk_size=200

 embs=model.encode(texts, convert_to_numpy=True, show_progress_bar=True, normalize_embeddings=True,batch_size=batch_size)


 with engine.begin() as cx:
  
    for chunk_id, v in zip(ids,embs):
        cx.exec_driver_sql(
            "INSERT INTO embeddings(chunk_id, vec) VALUES (%s,CAST(%s AS VECTOR))"
            "ON DUPLICATE KEY UPDATE vec=VALUES(vec)",
            (chunk_id, vec_to_text(v))
        )

print("Done.")