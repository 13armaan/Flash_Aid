# AI Health Navigator

**AI Health Navigator** is a CLI tool that answers health-related questions using a **Retrieval-Augmented Generation (RAG)** pipeline. 
It retrieves information from trusted medical sources, cites references, and (MVP goal) provides first-aid steps and nearest clinic suggestions. 

---

## 🚀 Features (MVP)
- **Web Data Loader** 
  - Fetches pages from trusted sources (WHO, NHS, CDC, data.gov.in). 
  - Cleans HTML → plain text. 
  - Splits long text into manageable chunks. 
  - Stores documents + chunks in a TiDB database. 
- **Planned CLI Q&A (RAG)** 
  - Ask health questions in plain English. 
  
  - Retrieves relevant chunks and feeds them to an LLM. 
  - Provides cited answers with links back to the source. 
  - Suggests nearby clinics for first aid. 

---

## ⚠️ License Disclaimer
The project includes a simple `guess_license()` helper that returns likely license strings based on source domains (e.g. WHO, NHS, CDC, GoI). 
This is **only a heuristic** and **not legally binding**. Always verify the official license from the source website before reuse. 

---

## 🛠️ Setup

### Requirements
- Python 3.10+ 
- TiDB (Cloud or local) 
- `.env` file with your database connection:
  ```env
  TIDB_DATABASE_URL=mysql+pymysql://user:pass@host:port/dbname

