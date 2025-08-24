from .tools import search_docs, first_aid, find_facility, translate
from core.models import AgentQuery,AgentAnswer

async def run_agent(q:AgentQuery) ->AgentAnswer:
    docs=await search_docs.search(q.question)
    answer,cites=search_docs.synthesize(docs)
    steps=first_aid.maybe_get_steps(q.question)
    facilities=[]
    if q.location_text:
        facilities=await find_facility.lookup(q.location_text)
    result=AgentAnswer(answer=answer,citation=cites,emergency_steps=steps,facilities=facilities,language=q.target_lang)
    if q.target_lang !="en":
        result=await translate.translate_payload(result,target_lang=q.target_lang)
    return result
