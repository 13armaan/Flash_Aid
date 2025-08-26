from fastapi import FastAPI
from src.core.models import AgentQuery
from src.agent.run_agent import run_agent

app=FastAPI()

@app.post("/agent")
async def agent_endpoint(q:AgentQuery):
    return await run_agent(q)

