import os
import json
from groq import Groq
from typing import Dict, Any, Optional
from app.config import settings

class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to initialize Groq client: {e}")

    def generate_explanation(self, question: str, intent: str, entities: dict, evidence: dict, deterministic_answer: str) -> Optional[str]:
        if not self.client:
            return None

        prompt = f"""
You are the conversational interface for the RoadSense system.
Your role is to explain the provided verified backend data to the user naturally.

Strict Rules:
- Use ONLY the supplied verified facts and evidence.
- Never invent facts, numbers, road IDs, damage IDs, or coordinates.
- Never override verified backend values.
- Do not perform authoritative calculations.
- Do not expose chain-of-thought.
- If evidence is insufficient, explicitly say that the available evidence is insufficient.
- Clearly distinguish verified backend information from your explanation.

Context:
Question: {question}
Detected Intent: {intent}
Extracted Entities: {json.dumps(entities)}

Verified Backend Data & Evidence:
{json.dumps(evidence)}

Deterministic Base Answer:
{deterministic_answer}

Provide a natural, helpful, and concise response using ONLY the facts above.
"""
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "system", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=500,
                timeout=10.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API Error: {e}")
            return None

groq_service = GroqService()
