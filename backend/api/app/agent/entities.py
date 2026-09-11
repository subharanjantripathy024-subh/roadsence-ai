import re
from typing import Dict, Any

class EntityExtractor:
    @staticmethod
    def extract_budget(text: str) -> float:
        """
        Extract budget considering Indian currency representations like:
        ₹10 lakh, 10 lakh, 10L, 5 lakhs, ₹500000
        """
        text_lower = text.lower()
        
        # Match standard numbers and currency symbols (e.g., ₹500000, 50000, $500)
        standard_match = re.search(r'(?:₹|\$|rs\.?|rupees?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?!lakh|l|k|m)', text_lower)
        
        # Match lakh representations (e.g., 10 lakh, 10 lakhs, 10L)
        lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakhs?|l)\b', text_lower)
        
        # Match thousand/k (e.g., 50k)
        k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text_lower)
        
        if lakh_match:
            return float(lakh_match.group(1)) * 100000.0
        elif k_match:
            return float(k_match.group(1)) * 1000.0
        elif standard_match:
            val = standard_match.group(1).replace(',', '')
            return float(val)
            
        return None

    @staticmethod
    def extract_entities(text: str) -> Dict[str, Any]:
        entities = {}
        
        # Road ID (e.g., r1, R12, road_1)
        road_id_matches = re.findall(r'\b(?:r|road[_\s]?)-?(\d+)\b', text, re.IGNORECASE)
        if road_id_matches:
            # Reconstruct as 'rX' as that's the format in demo data, but wait, the query could be R12, the ID might be r12
            entities['road_id'] = [f"r{rid}" for rid in road_id_matches]
            
        # Damage ID (e.g., dmg-001)
        dmg_id_match = re.search(r'\b(dmg-\d+)\b', text, re.IGNORECASE)
        if dmg_id_match:
            entities['damage_id'] = dmg_id_match.group(1).lower()
            
        # Severity
        severities = ["low", "medium", "high", "critical"]
        for sev in severities:
            if sev in text.lower():
                entities['severity'] = sev
                break
                
        # Damage Type
        types = ["pothole", "crack", "rutting"]
        for dt in types:
            if dt in text.lower():
                entities['damage_type'] = dt
                break

        # Budget
        budget = EntityExtractor.extract_budget(text)
        if budget is not None:
            entities['budget'] = budget
            
        # Coordinates
        lat_match = re.search(r'lat(?:itude)?\s*(-?\d+(?:\.\d+)?)', text, re.IGNORECASE)
        lon_match = re.search(r'lon(?:gitude)?\s*(-?\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if lat_match and lon_match:
            entities['latitude'] = float(lat_match.group(1))
            entities['longitude'] = float(lon_match.group(1))
            
        return entities

entity_extractor = EntityExtractor()
