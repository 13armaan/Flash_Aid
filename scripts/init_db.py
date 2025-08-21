import os, sqlalchemy as sa 
from dotenv import load_dotenv
load_dotenv()
url=os.environ["TIDB_DATABASE_URL"]
engine=sa.create_engine(url,pool_recycle=300)
schema= """
CREATE DATABASE IF NOT EXISTS ai_rag;
USE ai_rag;

CREATE TABLE IF NOT EXISTS documents(
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source VARCHAR(64),
    lang   VARCHAR(16),
    url    TEXT,
    title  TEXT,
    license Text
);

CREATE TABLE IF NOT EXISTS chunks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    doc_id BIGINT,
    seq INT,
    text MEDIUMTEXT,
    FOREIGN KEY(doc_id) REFERENCES documents(id)
);
CREATE TABLE IF NOT EXISTS embeddings(
    chunk_id BIGINT PRIMARY KEY,
    vec VECTOR(384),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);
CREATE TABLE IF NOT EXISTS faq(
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    q TEXT,
    a MEDIUMTEXT,
    lang VARCHAR(16)
);
CREATE TABLE IF NOT EXISTS queries(
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    q  TEXT,
    metadata JSON
);
ALTER TABLE embeddings SET TIFLASH REPLICA 1;
DROP INDEX IF EXISTS idx_vec ON embeddings;
CREATE VECTOR INDEX IF NOT EXISTS idx_vec ON embeddings((VEC_COSINE_DISTANCE(vec))) USING HNSW;
"""

with engine.begin() as cx:
    for stmt in[s.strip() for s in schema.split(';') if s.strip()]:
        cx.exec_driver_sql(stmt)

print("Database initialized")
