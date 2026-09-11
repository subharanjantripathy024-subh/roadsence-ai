from typing import Dict, Any

from app.agent.intent import intent_classifier
from app.agent.entities import entity_extractor
from app.agent.tools import tools
from app.models.evidence import Evidence
from app.agent.session import session_manager
from app.agent.groq_service import groq_service
from app.agent.validator import validator


class RoadSenseAgent:
    def __init__(self):
        self.classifier = intent_classifier
        self.extractor = entity_extractor
        self.tools = tools

    def process_request(
        self,
        question: str,
        session_id: str = "default"
    ) -> Dict[str, Any]:

        session = session_manager.get_session(session_id)

        # -----------------------------------------------------
        # FOLLOW-UP QUESTION
        # -----------------------------------------------------

        if (
            question.strip().lower() == "why?"
            and session["previous_intent"]
        ):
            intent = session["previous_intent"]
            entities = session["previous_filters"]
            confidence = 1.0
            is_follow_up = True

        else:
            intent_data = self.classifier.predict(question)

            intent = intent_data["intent"]
            confidence = intent_data["confidence"]

            entities = self.extractor.extract_entities(
                question
            )

            is_follow_up = False

        data = {}
        evidence_objs = []

        answer = (
            "I couldn't understand the request."
        )

        # -----------------------------------------------------
        # FOLLOW-UP
        # -----------------------------------------------------

        if (
            is_follow_up
            and session["last_evidence"]
        ):
            evidence_objs = [
                Evidence(**e)
                for e in session["last_evidence"]
            ]

            data = session["previous_result"]

            answer = (
                "Here is the explanation for the "
                "previous result based on the evidence."
            )

        else:

            # -------------------------------------------------
            # UNKNOWN
            # -------------------------------------------------

            if intent == "unknown":

                answer = (
                    "I'm sorry, I don't understand "
                    "that request."
                )

            # -------------------------------------------------
            # PRIORITY QUERY
            # -------------------------------------------------

            elif intent == "priority_query":

                data = (
                    self.tools
                    .get_high_priority_damages()
                )

                evidence_objs.append(
                    Evidence(
                        tool="get_high_priority_damages",
                        verified_facts={
                            "count": len(data),
                            "damages": data
                        }
                    )
                )

                if data:

                    # Priority 1 is the highest priority.
                    highest_priority = min(
                        int(
                            item.get(
                                "priority",
                                999
                            )
                        )
                        for item in data
                    )

                    highest_items = [
                        item
                        for item in data
                        if int(
                            item.get(
                                "priority",
                                999
                            )
                        )
                        == highest_priority
                    ]

                    # Count each damage type instead of
                    # repeating the same name many times.
                    damage_counts = {}

                    for item in highest_items:

                        damage_type = item.get(
                            "damage_type",
                            "unknown damage"
                        )

                        damage_counts[damage_type] = (
                            damage_counts.get(
                                damage_type,
                                0
                            ) + 1
                        )

                    damage_summary = ", ".join(
                        f"{count} {damage_type}"
                        for damage_type, count
                        in damage_counts.items()
                    )

                    answer = (
                        f"Priority {highest_priority} "
                        f"is the highest urgency level "
                        f"currently detected. "
                        f"There are {len(highest_items)} "
                        f"damage detections at this level: "
                        f"{damage_summary}. "
                        f"These require immediate attention."
                    )

                else:

                    # No Priority-1/high-priority records.
                    # Check the full current dataset.

                    all_damages = (
                        self.tools
                        .get_all_damages()
                        if hasattr(
                            self.tools,
                            "get_all_damages"
                        )
                        else []
                    )

                    if all_damages:

                        existing_priorities = [
                            int(
                                item.get(
                                    "priority",
                                    999
                                )
                            )
                            for item in all_damages
                            if item.get("priority")
                            is not None
                        ]

                        if existing_priorities:

                            best_priority = min(
                                existing_priorities
                            )

                            best_items = [
                                item
                                for item in all_damages
                                if int(
                                    item.get(
                                        "priority",
                                        999
                                    )
                                )
                                == best_priority
                            ]

                            priority_counts = {}

                            for item in best_items:

                                damage_type = item.get(
                                    "damage_type",
                                    "unknown damage"
                                )

                                priority_counts[
                                    damage_type
                                ] = (
                                    priority_counts.get(
                                        damage_type,
                                        0
                                    ) + 1
                                )

                            names = ", ".join(
                                f"{count} {damage_type}"
                                for damage_type, count
                                in priority_counts.items()
                            )

                            answer = (
                                "There are currently no "
                                "Priority 1/high-priority "
                                "damages. The highest "
                                f"priority currently present "
                                f"is Priority {best_priority}: "
                                f"{names}."
                            )

                        else:

                            answer = (
                                "There are no prioritized "
                                "damages in the current dataset."
                            )

                    else:

                        answer = (
                            "There are currently no high "
                            "priority damages in the dataset."
                        )

            # -------------------------------------------------
            # DAMAGE QUERY
            # -------------------------------------------------

            elif intent == "damage_query":

                dmg_id = entities.get(
                    "damage_id"
                )

                if dmg_id:

                    data = (
                        self.tools
                        .get_damage_by_id(
                            dmg_id
                        )
                    )

                    if "error" in data:

                        answer = (
                            f"Damage ID {dmg_id} "
                            "does not exist in the "
                            "current dataset."
                        )

                    else:

                        answer = (
                            f"Details for {dmg_id}: "
                            f"Type "
                            f"{data.get('damage_type')}, "
                            f"Severity "
                            f"{data.get('severity')}, "
                            f"Priority "
                            f"{data.get('priority')}."
                        )

                        evidence_objs.append(
                            Evidence(
                                tool="get_damage_by_id",
                                damage_ids=[
                                    dmg_id
                                ],
                                verified_facts={
                                    "damage": data
                                }
                            )
                        )

                else:

                    answer = (
                        "Please specify a damage ID."
                    )

            # -------------------------------------------------
            # DAMAGE STATISTICS
            # -------------------------------------------------

            elif intent == "damage_statistics":

                data = (
                    self.tools
                    .get_damage_statistics()
                )

                answer = (
                    f"There are a total of "
                    f"{data['total_damages']} damages. "
                    f"By type: {data['by_type']}"
                )

                evidence_objs.append(
                    Evidence(
                        tool="get_damage_statistics",
                        verified_facts=data
                    )
                )

            # -------------------------------------------------
            # SEVERITY
            # -------------------------------------------------

            elif intent == "severity_query":

                data = (
                    self.tools
                    .get_severity_statistics()
                )

                answer = (
                    f"Severity statistics: "
                    f"{data['by_severity']}"
                )

                evidence_objs.append(
                    Evidence(
                        tool="get_severity_statistics",
                        verified_facts=data
                    )
                )

            # -------------------------------------------------
            # COST
            # -------------------------------------------------

            elif intent == "cost_query":

                road_id = (
                    entities.get(
                        "road_id",
                        [None]
                    )[0]
                    if "road_id" in entities
                    else None
                )

                data = (
                    self.tools
                    .calculate_repair_cost(
                        road_id
                    )
                )

                target = (
                    f"road {road_id}"
                    if road_id
                    else "all roads"
                )

                answer = (
                    f"The estimated repair cost "
                    f"for {target} is "
                    f"{data['total_estimated_cost']}."
                )

                evidence_objs.append(
                    Evidence(
                        tool="calculate_repair_cost",
                        road_ids=(
                            [road_id]
                            if road_id
                            else []
                        ),
                        verified_facts=data
                    )
                )

            # -------------------------------------------------
            # BUDGET
            # -------------------------------------------------

            elif intent == "budget_optimization":

                budget = entities.get(
                    "budget"
                )

                if budget:

                    data = (
                        self.tools
                        .optimize_repairs_for_budget(
                            budget
                        )
                    )

                    answer = (
                        f"With a budget of "
                        f"{budget}, you can repair "
                        f"{data['repairs_selected_count']} "
                        f"damages. Total cost: "
                        f"{data['total_cost']}. "
                        f"Remaining budget: "
                        f"{data['remaining_budget']}."
                    )

                    evidence_objs.append(
                        Evidence(
                            tool="optimize_repairs_for_budget",
                            verified_facts=data
                        )
                    )

                else:

                    answer = (
                        "Please specify a budget amount."
                    )

            # -------------------------------------------------
            # ROAD COMPARISON
            # -------------------------------------------------

            elif intent == "road_comparison":

                road_ids = entities.get(
                    "road_id",
                    []
                )

                if len(road_ids) >= 2:

                    data = (
                        self.tools
                        .compare_roads(
                            road_ids
                        )
                    )

                    answer = (
                        f"Comparison for "
                        f"{', '.join(road_ids)}: "
                        f"{data}"
                    )

                    evidence_objs.append(
                        Evidence(
                            tool="compare_roads",
                            road_ids=road_ids,
                            verified_facts=data
                        )
                    )

                else:

                    answer = (
                        "Please specify at least "
                        "two road IDs to compare."
                    )

            # -------------------------------------------------
            # LOCATION
            # -------------------------------------------------

            elif intent == "location_query":

                lat = entities.get(
                    "latitude"
                )

                lon = entities.get(
                    "longitude"
                )

                if lat and lon:

                    data = (
                        self.tools
                        .search_damage_by_location(
                            lat,
                            lon
                        )
                    )

                    answer = (
                        f"Found "
                        f"{len(data['matches'])} "
                        "damages near the location."
                    )

                    evidence_objs.append(
                        Evidence(
                            tool="search_damage_by_location",
                            verified_facts=data
                        )
                    )

                else:

                    answer = (
                        "Please specify latitude "
                        "and longitude."
                    )

            # -------------------------------------------------
            # SUMMARY
            # -------------------------------------------------

            elif intent == "summary_query":

                stats = (
                    self.tools
                    .get_damage_statistics()
                )

                costs = (
                    self.tools
                    .calculate_repair_cost()
                )

                data = {
                    "statistics": stats,
                    "costs": costs
                }

                answer = (
                    f"Overall summary: "
                    f"{stats['total_damages']} "
                    f"damages total. "
                    f"Estimated cost: "
                    f"{costs['total_estimated_cost']}."
                )

                evidence_objs.append(
                    Evidence(
                        tool="summary_query",
                        verified_facts=data
                    )
                )

            # -------------------------------------------------
            # GENERAL
            # -------------------------------------------------

            elif intent == "general_roadsense":

                answer = (
                    "RoadSense is a platform for "
                    "detecting, classifying, and "
                    "prioritizing road damage using "
                    "computer vision and AI orchestration."
                )

        # -----------------------------------------------------
        # EVIDENCE
        # -----------------------------------------------------

        evidence_dicts = [
            e.model_dump()
            for e in evidence_objs
        ]

        # -----------------------------------------------------
        # GROQ OPTIONAL EXPLANATION
        # -----------------------------------------------------

        final_answer = answer

        if (
            evidence_dicts
            and intent != "unknown"
            and intent != "general_roadsense"
        ):

            groq_response = (
                groq_service.generate_explanation(
                    question,
                    intent,
                    entities,
                    evidence_dicts,
                    answer
                )
            )

            if groq_response:

                is_valid = (
                    validator.validate_numbers(
                        groq_response,
                        evidence_dicts
                    )
                )

                if is_valid:
                    final_answer = groq_response

        # -----------------------------------------------------
        # SESSION
        # -----------------------------------------------------

        session_manager.update_session(
            session_id,
            {
                "previous_intent": intent,

                "previous_road_ids":
                    entities.get(
                        "road_id",
                        []
                    ),

                "previous_damage_ids": (
                    [entities.get("damage_id")]
                    if entities.get("damage_id")
                    else []
                ),

                "previous_filters":
                    entities,

                "previous_result":
                    data,

                "last_evidence":
                    evidence_dicts,
            }
        )

        # -----------------------------------------------------
        # RESPONSE
        # -----------------------------------------------------

        return {
            "answer": final_answer,
            "intent": intent,
            "confidence": confidence,
            "evidence": evidence_dicts,
            "data": data
        }


agent = RoadSenseAgent()