from fastapi import FastAPI
import logging
from core.models import AgentQuery
from core.models import AgentAnswer
from agent.run_agent import run_agent

app=FastAPI()

@app.get("/")
def root():
    return {"Message":"AI Health Navigator server is running"}

@app.post("/ask")
async def agent_endpoint(q:AgentQuery):
    """
    Main endpoint: pass in your query
    """
    try:
        return await run_agent(q)
    except Exception as e:
        logging.error("Error in /ask endpoint: %s",e)
        traceback.print_exc()
        return{"answer":"Something Went Wrong","citations":[],"emergency_steps":[],"facilities":[],"language":"en"}
