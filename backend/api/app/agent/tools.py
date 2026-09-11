import math
from typing import List, Dict, Any
from app.data.repository import repository
from app.models.domain import DamageInstance

class DeterministicTools:
    
    @staticmethod
    def get_all_damages() -> List[Dict[str, Any]]:
        return [d.model_dump() for d in repository.get_all_damages()]

    @staticmethod
    def get_damage_by_id(damage_id: str) -> Dict[str, Any]:
        d = repository.get_damage_by_id(damage_id)
        if not d:
            return {"error": f"Damage ID {damage_id} not found."}
        return d.model_dump()

    @staticmethod
    def get_damage_statistics() -> Dict[str, Any]:
        damages = repository.get_all_damages()
        count = len(damages)
        types = {}
        for d in damages:
            types[d.damage_type] = types.get(d.damage_type, 0) + 1
        return {"total_damages": count, "by_type": types}

    @staticmethod
    def get_severity_statistics() -> Dict[str, Any]:
        damages = repository.get_all_damages()
        severities = {}
        for d in damages:
            severities[d.severity] = severities.get(d.severity, 0) + 1
        return {"by_severity": severities}

    @staticmethod
    def get_high_priority_damages() -> List[Dict[str, Any]]:
        # Assume priority 1 is highest
        damages = repository.get_damages_by_priority()
        return [d.model_dump() for d in damages if d.priority <= 2]

    @staticmethod
    def compare_roads(road_ids: List[str]) -> Dict[str, Any]:
        damages = repository.get_all_damages()
        comparison = {}
        for rid in road_ids:
            r_damages = [d for d in damages if d.road_id == rid]
            total_cost = sum(d.estimated_repair_cost for d in r_damages)
            comparison[rid] = {
                "damage_count": len(r_damages),
                "total_repair_cost": total_cost,
                "critical_damages": sum(1 for d in r_damages if d.severity == "critical")
            }
        return comparison

    @staticmethod
    def calculate_repair_cost(road_id: str = None) -> Dict[str, Any]:
        damages = repository.get_all_damages()
        if road_id:
            damages = [d for d in damages if d.road_id == road_id]
        total = sum(d.estimated_repair_cost for d in damages)
        return {"road_id": road_id or "all", "total_estimated_cost": total, "damage_count": len(damages)}

    @staticmethod
    def optimize_repairs_for_budget(budget: float) -> Dict[str, Any]:
        damages = repository.get_all_damages()
        
        # Sort by priority (asc, 1 is highest) then cost (asc, cheapest first)
        severity_rank = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        
        sorted_damages = sorted(damages, key=lambda x: (
            x.priority, 
            severity_rank.get(x.severity, 99),
            x.estimated_repair_cost
        ))
        
        selected = []
        total_cost = 0.0
        
        for d in sorted_damages:
            if total_cost + d.estimated_repair_cost <= budget:
                selected.append(d)
                total_cost += d.estimated_repair_cost
                
        return {
            "initial_budget": budget,
            "total_cost": total_cost,
            "remaining_budget": budget - total_cost,
            "repairs_selected_count": len(selected),
            "repairs": [s.model_dump() for s in selected]
        }

    @staticmethod
    def search_damage_by_location(lat: float, lon: float, radius_km: float = 5.0) -> Dict[str, Any]:
        damages = repository.get_all_damages()
        results = []
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0 # Earth radius in km
            dLat = math.radians(lat2 - lat1)
            dLon = math.radians(lon2 - lon1)
            a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        for d in damages:
            dist = haversine(lat, lon, d.latitude, d.longitude)
            if dist <= radius_km:
                results.append({"distance_km": round(dist, 2), "damage": d.model_dump()})
                
        results = sorted(results, key=lambda x: x["distance_km"])
        return {"center": {"latitude": lat, "longitude": lon}, "radius_km": radius_km, "matches": results}

tools = DeterministicTools()
