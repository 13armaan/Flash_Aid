from .tools import search_docs, first_aid, find_facility, translate, build_prompt,call_llm
from core.models import AgentQuery,AgentAnswer

async def run_agent(q:AgentQuery) ->AgentAnswer:
    content,cites=search_docs.retrieve(q.question)
    prompt=build_prompt.prompt(q.question,content)
    answer=call_llm.call(prompt)
    steps=first_aid.steps(q.question)
    facilities=[]
    if q.lat and q.lon:
        facilities=await find_facility.lookup(lat=q.lat,lon=q.lon)
    elif q.location_text:
        facilities=await find_facility.lookup(location_text=q.location_text)
   
    result=AgentAnswer(answer=answer,citations=cites,emergency_steps=steps,facilities=facilities,language=q.target_lang)
    if q.target_lang !="en":
        result=await translate.translate_payload(result,target_lang=q.target_lang)
  
    return result
   