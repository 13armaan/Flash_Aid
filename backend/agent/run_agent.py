from .tools import search_docs, first_aid, find_facility, translate, build_prompt,call_llm
from core.models import AgentQuery,AgentAnswer,latencyEach
import time
import  asyncio


def format_metadata(facilities,citations):
    lines=[]
    if facilities:
        lines.append("## 🏥 Nearby Facilities ##\n")
        for i, f in enumerate(facilities,start=1):
            lines.append(f" 🏥 {i}. {f.name} ({f.distance_km} km)\n")
            lines.append(f"[View on map]({f.map_url})\n")
        lines.append("")
    
    if citations:
        lines.append("## 📚 References ##\n")
        for i,c in enumerate(citations,start=1):
            lines.append(f"[{i}] {c.title}")
            lines.append(f"{c.url}")
        lines.append("")
    return "\n".join(lines)

async def run_agent_stream(q:AgentQuery):
    search_task=asyncio.create_task( search_docs.retrieve(q.question))
    steps_task=asyncio.create_task(first_aid.steps(q.question))
    fac_task=None
    if q.lat and q.lon:
        fac_task=asyncio.create_task(find_facility.lookup(lat=q.lat,lon=q.lon))
    elif q.location_text:
        fac_task=asyncio.create_task(find_facility.lookup(location_text=q.location_text))
    

    content,cites=await search_task
    prompt=await build_prompt.prompt(q.question,content)
    steps=await steps_task
    if fac_task:
        facs=await fac_task
    async for token in call_llm.call_llm_stream(prompt):
        yield {
            "type":"token",
            "content":token
        }
    
    yield{
        "type":"metadata",
        "content": {
            "facilities":[f.dict() for f in facs] if facs else [],
            "citations":[c.dict() for c in cites] if cites else []
        }
    }
    
    
async def run_agent_normal(q:AgentQuery) ->AgentAnswer:
    lat=[]
    t0=time.perf_counter()

    search_task=asyncio.create_task( search_docs.retrieve(q.question))
    steps_task=asyncio.create_task(first_aid.steps(q.question))
    fac_task=None
    if q.lat and q.lon:
        fac_task=asyncio.create_task(find_facility.lookup(lat=q.lat,lon=q.lon))
    elif q.location_text:
        fac_task=asyncio.create_task(find_facility.lookup(location_text=q.location_text))
        

    content,cites=await search_task
    t1=time.perf_counter()
    top_content=content[:3]
    lat.append(latencyEach(title="search",time=round(t1-t0,3)))
    prompt=await build_prompt.prompt(q.question,top_content)
    t2=time.perf_counter()
    lat.append(latencyEach(title="prompt",time=round(t2-t1,3)))
    answer=await  call_llm.call_llm_normal(prompt)
    t3=time.perf_counter()
    lat.append(latencyEach(title="llm",time=round(t3-t2,3)))
    steps=await steps_task
    t4=time.perf_counter()
    lat.append(latencyEach(title="steps",time=round(t4-t3,3)))
    facilities=[]
    t5=None
    t6=None
    if fac_task:
        facilities=await fac_task
        t5=time.perf_counter()
        lat.append(latencyEach(title="fac",time=round(t5-t4,3)))
    
    result=AgentAnswer(answer=answer,citations=cites,emergency_steps=steps,facilities=facilities,language=q.target_lang,latency=lat)
    if q.target_lang !="en":
        
        tran= await translate.async_translate(result,"en",q.target_lang)
        t6=time.perf_counter()
        if t5:
            lat.append(latencyEach(title="transl",time=round(t5-t4,3)))
        else:
            lat.append(latencyEach(title="transl",time=round(t6-t4,3)))
        result.answer=tran
        result.language=q.target_lang
        result.latency=lat
    return result
   