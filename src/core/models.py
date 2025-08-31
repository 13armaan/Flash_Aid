from pydantic import BaseModel
from typing import List,Optional

class citation(BaseModel):
    title:str
    url:str

class step(BaseModel):
    steps:list[str]

class facility(BaseModel):
    name:str
    distance_km: float
    phone:Optional[str]
    opening_hours: Optional[str]
    map_url:str

class AgentAnswer(BaseModel):
    answer:str
    citations:List [citation]=[]
    emergency_steps:List[step]=[]
    facilities :List[facility]=[]
    language:str="en"
    latency:Optional[float]=None

class AgentQuery(BaseModel):
    question: str
    location_text:Optional[str]=None
    lat:Optional[float]=None
    lon:Optional[float]=None
    target_lang:str="en"

