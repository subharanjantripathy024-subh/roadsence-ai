from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import numpy as np


TRAINING_DATA = [

    # =========================================================
    # PRIORITY QUERY
    # =========================================================

    ("Which road should I repair first?", "priority_query"),
    ("What are the most urgent repairs?", "priority_query"),
    ("Show me high priority damages", "priority_query"),
    ("Top priority roads", "priority_query"),
    ("What needs immediate attention?", "priority_query"),
    ("Which road is worst?", "priority_query"),
    ("Worst road", "priority_query"),
    ("Which damage needs the highest priority?", "priority_query"),
    ("Which damage should be repaired first?", "priority_query"),
    ("What damage should get attention first?", "priority_query"),
    ("Which repair is most important?", "priority_query"),
    ("Show the most important repairs", "priority_query"),
    ("What should we repair first?", "priority_query"),
    ("Which pothole needs immediate attention?", "priority_query"),
    ("What is the highest priority damage?", "priority_query"),

    # =========================================================
    # DAMAGE QUERY
    # =========================================================

    ("Find damage dmg-001", "damage_query"),
    ("Tell me about pothole on Main St", "damage_query"),
    ("What is the status of damage 5?", "damage_query"),
    ("Show me damage info", "damage_query"),
    ("Details for damage id 123", "damage_query"),
    ("What is the condition of road r1?", "damage_query"),
    ("What is the condition of road", "damage_query"),
    ("Give details about this damage", "damage_query"),
    ("Tell me about damage 123", "damage_query"),
    ("Show details for this road damage", "damage_query"),

    # =========================================================
    # DAMAGE STATISTICS
    # =========================================================

    ("How many damages are there?", "damage_statistics"),
    ("Count the potholes", "damage_statistics"),
    ("Total number of cracks", "damage_statistics"),
    ("Give me the damage count", "damage_statistics"),
    ("Statistics of damages", "damage_statistics"),
    ("How many potholes are detected?", "damage_statistics"),
    ("How many cracks are there?", "damage_statistics"),
    ("How many road damages are detected?", "damage_statistics"),
    ("What is the total number of damages?", "damage_statistics"),
    ("Give me damage statistics", "damage_statistics"),
    ("How many issues were found?", "damage_statistics"),

    # =========================================================
    # SEVERITY QUERY
    # =========================================================

    ("What are the most severe damages?", "severity_query"),
    ("Show me critical severity", "severity_query"),
    ("List low severity issues", "severity_query"),
    ("Which damages are severe?", "severity_query"),
    ("Filter by high severity", "severity_query"),
    ("Show critical damages", "severity_query"),
    ("How many critical damages are there?", "severity_query"),
    ("Which damages have high severity?", "severity_query"),
    ("Show medium severity damages", "severity_query"),

    # =========================================================
    # COST QUERY
    # =========================================================

    ("How much will repairs cost?", "cost_query"),
    ("What is the total estimated cost?", "cost_query"),
    ("Cost of repairing road 1", "cost_query"),
    ("Tell me the repair cost", "cost_query"),
    ("Total budget required", "cost_query"),
    ("What will the repairs cost?", "cost_query"),
    ("How expensive are the repairs?", "cost_query"),
    ("What is the estimated repair cost?", "cost_query"),
    ("How much money is needed for repairs?", "cost_query"),
    ("What is the total repair expense?", "cost_query"),
    ("How much does road repair cost?", "cost_query"),
    ("How much money will repairs require?", "cost_query"),
    ("What is the cost of all repairs?", "cost_query"),
    ("What will it cost to repair the roads?", "cost_query"),
    ("How much will the road repairs cost?", "cost_query"),

    # =========================================================
    # BUDGET OPTIMIZATION
    # =========================================================

    ("I have ₹10 lakh. What should I repair?", "budget_optimization"),
    ("I only have 50000 budget, optimize repairs", "budget_optimization"),
    ("What can I fix with 5 lakhs?", "budget_optimization"),
    ("Optimize repairs for 1000 dollars", "budget_optimization"),
    ("Best repairs for 20k", "budget_optimization"),

    ("I have a budget of 6000. Which damages should be repaired?", "budget_optimization"),
    ("I have 6000 rupees. What should I repair?", "budget_optimization"),
    ("What can I repair with a budget of 6000?", "budget_optimization"),
    ("Which damages can be repaired within 6000?", "budget_optimization"),
    ("What should I fix with 6000?", "budget_optimization"),
    ("Which repairs should I choose with 6000?", "budget_optimization"),
    ("I have only 6000 available for repairs", "budget_optimization"),
    ("How should I spend 6000 on road repairs?", "budget_optimization"),
    ("Use my 6000 budget to optimize repairs", "budget_optimization"),
    ("With a budget of 6000 which roads can I repair?", "budget_optimization"),
    ("What repairs fit within my budget?", "budget_optimization"),
    ("Which damages fit within my budget?", "budget_optimization"),
    ("What can be fixed within the available budget?", "budget_optimization"),
    ("I have limited funds. Which repairs should I prioritize?", "budget_optimization"),
    ("If my repair budget is 6000, what should I repair?", "budget_optimization"),
    ("Given 6000 rupees, which damages should be repaired?", "budget_optimization"),
    ("I have 6000 to spend on road repairs", "budget_optimization"),
    ("How can I optimize repairs with 6000?", "budget_optimization"),

    # =========================================================
    # ROAD COMPARISON
    # =========================================================

    ("Compare R12 and R15.", "road_comparison"),
    ("Which is worse, road A or road B?", "road_comparison"),
    ("Compare damage on Market St and Mission St", "road_comparison"),
    ("Show comparison between r1 and r2", "road_comparison"),
    ("Compare roads", "road_comparison"),
    ("Which road is better?", "road_comparison"),

    # =========================================================
    # LOCATION QUERY
    # =========================================================

    ("Find damages near me", "location_query"),
    ("What's around latitude 37 longitude -122?", "location_query"),
    ("Show issues within 5km of my location", "location_query"),
    ("Search by location", "location_query"),
    ("Damages near these coordinates", "location_query"),
    ("Find road damage near this location", "location_query"),
    ("Show damages around these coordinates", "location_query"),

    # =========================================================
    # SUMMARY QUERY
    # =========================================================

    ("Give me a summary of road conditions.", "summary_query"),
    ("Overall road network status", "summary_query"),
    ("Summary report", "summary_query"),
    ("Provide a quick summary", "summary_query"),
    ("What's the overall summary?", "summary_query"),
    ("Give me an overall report", "summary_query"),
    ("Summarize the current road condition", "summary_query"),

    # =========================================================
    # GENERAL ROADSENSE
    # =========================================================

    ("What is RoadSense?", "general_roadsense"),
    ("How does this app work?", "general_roadsense"),
    ("Who made this?", "general_roadsense"),
    ("Help me use this system", "general_roadsense"),
    ("What can you do?", "general_roadsense"),
    ("Explain RoadSense", "general_roadsense"),
]


class IntentClassifier:

    def __init__(self):

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True
        )

        self.classifier = LogisticRegression(
            class_weight="balanced",
            C=2.0,
            max_iter=1000
        )

        X_text = [
            text
            for text, intent in TRAINING_DATA
        ]

        self.y = [
            intent
            for text, intent in TRAINING_DATA
        ]

        self.X = self.vectorizer.fit_transform(
            X_text
        )

        self.classifier.fit(
            self.X,
            self.y
        )

    def predict(self, text: str):

        text_lower = text.lower().strip()

        # =====================================================
        # COST QUERY OVERRIDE
        # =====================================================
        # Handle direct repair-cost questions before the ML
        # classifier gets a chance to confuse them with budget
        # optimization.

        cost_keywords = [
            "repair cost",
            "repair costs",
            "repairs cost",
            "repairs costs",
            "repair expense",
            "repair expenses",
            "estimated cost",
            "estimated repair",
            "how much will repairs cost",
            "what will the repairs cost",
            "how expensive are the repairs",
            "how much money is needed for repairs",
            "how much does road repair cost",
            "cost of repairs",
            "cost of repairing",
            "total repair cost",
            "total repair expense",
            "total estimated cost",
        ]

        has_cost_question = any(
            keyword in text_lower
            for keyword in cost_keywords
        )

        # If the question contains a specific budget, it
        # should remain a budget-optimization question.
        has_budget_number = any(
            token.isdigit()
            for token in text_lower.replace(",", " ").split()
        )

        budget_context_keywords = [
            "budget",
            "₹",
            "rupees",
            "rs ",
            "rs.",
            "lakh",
            "lakhs",
            "spend",
            "spending",
            "funds",
            "available money",
        ]

        has_budget_context = any(
            keyword in text_lower
            for keyword in budget_context_keywords
        )

        if (
            has_cost_question
            and not (
                has_budget_context
                and has_budget_number
            )
        ):
            return {
                "intent": "cost_query",
                "confidence": 1.0
            }

        # =====================================================
        # BUDGET QUERY OVERRIDE
        # =====================================================

        budget_keywords = [
            "budget",
            "₹",
            "rupees",
            "rs ",
            "rs.",
            "lakh",
            "lakhs",
            "spend",
            "spending",
            "funds",
            "available money",
        ]

        repair_action_keywords = [
            "repair",
            "repairs",
            "repairing",
            "fix",
            "fixing",
            "repaired",
            "should i repair",
            "should i fix",
            "what can i repair",
            "what can i fix",
            "which damages",
            "which roads",
        ]

        has_budget = any(
            keyword in text_lower
            for keyword in budget_keywords
        )

        has_repair_action = any(
            keyword in text_lower
            for keyword in repair_action_keywords
        )

        if (
            has_budget
            and has_repair_action
        ):
            return {
                "intent": "budget_optimization",
                "confidence": 1.0
            }

        # =====================================================
        # NORMAL ML CLASSIFICATION
        # =====================================================

        X_new = self.vectorizer.transform(
            [text]
        )

        probabilities = (
            self.classifier
            .predict_proba(X_new)[0]
        )

        max_prob_index = np.argmax(
            probabilities
        )

        confidence = probabilities[
            max_prob_index
        ]

        intent = (
            self.classifier
            .classes_[max_prob_index]
        )

        # =====================================================
        # LOW CONFIDENCE
        # =====================================================

        if confidence < 0.15:
            return {
                "intent": "unknown",
                "confidence": float(
                    confidence
                )
            }

        return {
            "intent": intent,
            "confidence": float(
                confidence
            )
        }


intent_classifier = IntentClassifier()