import os
from loguru import logger

os.makedirs("logs", exist_ok=True)

logger.add("logs/agent.log", rotation-"1 MB", retention="10 days",level="INFO")

def log_query(query,tool_used,latency):
    logger.info(f"tool={tool_used},latency={latency:.2f}s")