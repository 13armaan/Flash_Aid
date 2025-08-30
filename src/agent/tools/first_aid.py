import json
from core.models import step
import os
DATA_PATH = os.path.join(os.path.dirname(__file__), "../../../data/first_aid.json")

with open(DATA_PATH,"r",encoding="utf-8") as f:
    db=json.load(f)
def steps(q:str) -> list[str]:
    q=q.lower().strip()
    result=db.get(
        q,["I dont have first-aid instructions for this. Please seek medical help immediately"]
    )
    out=[]
    out.append(step(
        steps=result
    ))
    return out
if __name__=="__main__":
    import sys
    if len(sys.argv)<2:
        print("Usage: python src/tools/first_aid.py \"condition\"")
        sys.exit(1)
    cond=sys.argv[1]
    print(steps(cond))