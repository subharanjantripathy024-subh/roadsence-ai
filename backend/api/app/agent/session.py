from typing import Dict, Any, Optional

class SessionContext:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "previous_intent": None,
                "previous_road_ids": [],
                "previous_damage_ids": [],
                "previous_filters": {},
                "previous_result": None,
                "last_evidence": None,
            }
        return self.sessions[session_id]

    def update_session(self, session_id: str, data: Dict[str, Any]):
        session = self.get_session(session_id)
        session.update(data)

session_manager = SessionContext()
