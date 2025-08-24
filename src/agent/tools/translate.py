from core.models import AgentAnswer
async def translate_payload(ans:AgentAnswer,target_lang:str)->AgentAnswer:
    return ans