from fastapi import FastAPI
from core.models import AgentQuery
from agent.agent import run_agent

app=FastAPI()

@app.post("/agent")
async def agent_endpoint(q:AgentQuery):
    return await run_agent(q)

