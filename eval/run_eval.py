import json,time,httpx,csv
from metrics import hit_rate_at_k, groundedness,contains_expected_facts

API="http://localhost:8000/ask"
EVAL="eval_set.json"
OUT="results.csv"

with open(EVAL) as f: cases=json.load(f)

rows=[]
with httpx.Client(timeout=60) as Client:
    for c in cases:
        payload={
            "question":c["question"],
            "location_text":"Delhi",
            "target_language":"en",
        }
        t0=time.time()
        r=Client.post(API,json=payload)
        t1=time.time()
        data=r.json()
        ans=data.get("answer","")
        cits=data.get("citations",[])
        retrieved=c.get("retrieved",cits)

        rows.append({
            "id":c["id"],
            "facts_score": contains_expected_facts(ans,c["expected_facts"]),
            "hit@5": hit_rate_at_k(retrieved,c["expected_citations"],5),
            "groundedness": groundedness(cits,c["expected_citations"]),
            "latency_ms":int((t1-t0)*1000)
        })

with open(OUT,"w",newline="") as f:
    w=csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

import statistics as st

print("facts:", round(st.mean(r["facts_score"] for r in rows),3))
print("hit@5:", round(st.mean(r["hit@5"] for r in rows),3))
print("grounded:", round(st.mean(r["groundedness"] for r in rows),3))
print("p95 latency:",sorted(r["latency_ms"] for r in rows)[int(0.95*len(rows))-1])