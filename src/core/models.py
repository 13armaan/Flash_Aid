from pydantic import BaseModel
from typing import List,Optional

class facility(BaseModel):
    name:str
    distance_km: float
    phone:Optional[str]
    opening_hours: Optional[str]
    map_url:str

class AgentAnswer(BaseModel):
    answer:str
    citations:List [str]=[]
    emergency_steps:List[str]=[]
    facilities :List[facility]=[]
    language:str="en"

class AgentQuery(BaseModel):
    question: str
    location_text:Optional[str]=None
    target_lang:str="en"