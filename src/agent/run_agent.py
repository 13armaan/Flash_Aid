from .tools import search_docs, first_aid, find_facility, translate, build_prompt,call_llm
from core.models import AgentQuery,AgentAnswer,latencyEach
import time
import  asyncio

async def run_agent(q:AgentQuery) ->AgentAnswer:
    lat=[]
    t0=time.perf_counter()
    content,cites=await  search_docs.retrieve(q.question)
    t1=time.perf_counter()
    lat.append(latencyEach(title="search",time=round(t1-t0,3)))
    prompt=await build_prompt.prompt(q.question,content)
    t2=time.perf_counter()
    lat.append(latencyEach(title="prompt",time=round(t2-t1,3)))
    answer=await  call_llm.call(prompt)
    t3=time.perf_counter()
    lat.append(latencyEach(title="llm",time=round(t3-t2,3)))
    steps=await  first_aid.steps(q.question)
    t4=time.perf_counter()
    lat.append(latencyEach(title="steps",time=round(t4-t3,3)))
    facilities=[]
    t5=None
    t6=None
    if q.lat and q.lon:
        facilities=await find_facility.lookup(lat=q.lat,lon=q.lon)
        t5=time.perf_counter()
        lat.append(latencyEach(title="fac",time=round(t5-t4,3)))
    elif q.location_text:
        facilities=await find_facility.lookup(location_text=q.location_text)
        t6=time.perf_counter()
        lat.append(latencyEach(title="fac",time=round(t6-t4,3)))
    
    result=AgentAnswer(answer=answer,citations=cites,emergency_steps=steps,facilities=facilities,language=q.target_lang,latency=lat)
    if q.target_lang !="en":
        try:
            await translate.install_package("en",q.target_lang)
        except ValueError:
            pass
        tran= translate.translate_payload(result,"en",q.target_lang)
        t7=time.perf_counter()
        if t6:
            lat.append(latencyEach(title="transl",time=round(t7-t6,3)))
            print(t6)
        elif t5:
            lat.append(latencyEach(title="transl",time=round(t7-t5,3)))
            print(t5)
            result.answer=tran
            result.language=q.target_lang
            result.latency=lat
    return result
   