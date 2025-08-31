import time,re
from typing import List,Dict,Any 

def hit_rate_at_k(retrieved: List[str],expected_domains:List[str],k:int =5)->int:
    got =any(any(dom in r for dom in expected_domains) for r in retrieved[:k])
    return int(got)

def groundedness(citations:List[str],expected_domains:List[str])->float:
    if not citations: return 0.0
    cite_domains={re.sub(r"^https?://(www\.)?","",c["url"]).split("/")[0] for c in citations if "url" in c}
    exp=set(expected_domains)
    inter= len(cite_domains & exp)
    union= len(cite_domains | exp)
    return inter/union if union else 0.0

def contains_expected_facts(answer: str,expected_facts:list[str])->float:
        found =sum(1 for f in expected_facts if f.lower() in answer.lower())
        return found/max(1,len(expected_facts))