from pydantic import BaseModel
from typing import Optional


class DamageInstance(BaseModel):
    damage_id: str
    road_id: str
    road_name: Optional[str] = None
    damage_type: str
    severity: str
    priority: int
    estimated_repair_cost: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        extra = "allow"


class M1Detection(BaseModel):
    detection_id: str
    timestamp: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    road_id: str
    damage_type: str
    confidence: float
    frame_id: str
    severity: Optional[str] = None
    priority: Optional[int] = None

    class Config:
        extra = "allow"