import os,numpy as np,sqlalchemy as sa
from sqlalchemy import text as sql
from dotenv import load_dotenv
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

load_dotenv()
engine=sa.create_engine(os.environ["TIDB_DATABASE_URL"], pool_recycle=300)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def vec_to_text(v):
    return "["+",".join(f"{x:.6f}" for x in v.tolist())+"]"

with engine.begin() as cx:
    rows=cx.exec_driver_sql(
        """
        SELECT c.id, c.text
        FROM chunks c
        LEFT JOIN embeddings e ON e.chunk_id=c.id
        WHERE e.chunk_id IS NULL
        ORDER by c.id
        LIMIT 100000
        """
        ).fetchall()
    
embs=model.encode([r[1] for r in rows], convert_to_numpy=True, show_progress_bar=True, normalize_embeddings=True)

with engine.begin() as cx:
    for(chunk_id,_), v in tqdm(zip(rows,embs), total=len(rows),desc="Embedding"):
        cx.exec_driver_sql(
            "INSERT INTO embeddings(chunk_id, vec) VALUES (%s,CAST(%s AS VECTOR))"
            "ON DUPLICATE KEY UPDATE vec=VALUES(vec)",
            (chunk_id, vec_to_text(v))
        )

print("Done.")