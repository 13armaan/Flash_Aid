from fastapi import FastAPI
import logging
from core.models import AgentQuery
from core.models import AgentAnswer , latencyEach
from agent.run_agent import run_agent_normal,run_agent_stream
import   traceback
import time
from concurrent.futures import ThreadPoolExecutor
from agent.tools import translate
from fastapi.responses import StreamingResponse
from fastapi import Query
import asyncio
import json

app=FastAPI()


INSTALLED_LANGUAGES=[]

@app.get("/")
def root():
    return {"Message":"AI Health Navigator server is running"}

@app.on_event("startup")
async def preload_packages():
    global INSTALLED_LANGUAGES
    try:
        await translate.install_package("en","hi")
        await translate.install_package("en","bn")
    except Exception as e:
        print("Erro loading packages",e)
    
@app.post("/ask")
async def agent_endpoint(q:AgentQuery,stream:bool=Query(False)):
    
    """
    Main endpoint: pass in your query
    """
    if stream:
        async def token_generator():
            async for token in run_agent_stream(q):
                yield f"data: {json.dumps(token)}\n\n"
                await asyncio.sleep(0)
            yield "data: [DONE]\n\n"
        return StreamingResponse(token_generator(),media_type="text/event-stream")
        
    else:
        try:
        
            result= await run_agent_normal(q)

            if not result:
             return AgentAnswer(
             answer="Sorry, I couldnt process your question",
             citations=[],
             emergency_steps=[],
             facilities=[],
             language="en",
             latency=None
        )
            return result
        except Exception as e:
            logging.error("Error in /ask endpoint: %s",e)
            traceback.print_exc()
            return{"answer":"Something Went Wrong","citations":[],"emergency_steps":[],"facilities":[],"language":"en"}
