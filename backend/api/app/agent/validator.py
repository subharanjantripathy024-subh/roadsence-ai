import re
from typing import Dict, Any

class ResponseValidator:
    @staticmethod
    def validate_numbers(groq_response: str, evidence: dict) -> bool:
        """
        Validates that numbers (counts, costs) mentioned in the Groq response 
        do not conflict with the authoritative evidence.
        Returns True if safe, False if a hallucinated factual claim is detected.
        """
        # Extract all numbers from groq response
        response_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', groq_response)
        
        # Extract all numbers from evidence (flattening string representations of dicts/lists)
        evidence_str = str(evidence)
        evidence_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', evidence_str)
        
        # If groq response contains numbers not found in evidence at all,
        # it might be hallucinating facts. 
        # But we shouldn't be overly strict (e.g. standard conversational numbers like "1 of them").
        # So this is a lightweight validation: if it contains a large unrecognized number, flag it.
        
        evidence_numbers_set = set(evidence_numbers)
        
        for num_str in response_numbers:
            # We ignore small numbers like 0, 1, 2 which might just be conversational.
            # We validate larger numbers (counts, IDs, costs, etc.)
            try:
                num = float(num_str)
                if num > 10 and num_str not in evidence_numbers_set:
                    # Flag as potential hallucination
                    return False
            except ValueError:
                pass
                
        return True

validator = ResponseValidator()
