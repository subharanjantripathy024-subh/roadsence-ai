from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Evidence(BaseModel):
    source: str = "DataRepository"
    tool: str
    road_ids: List[str] = []
    damage_ids: List[str] = []
    verified_facts: Dict[str, Any] = {}
