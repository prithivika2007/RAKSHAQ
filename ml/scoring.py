"""
Rakshaq Commute Safety Prototype - Driver Trust Scoring
========================================================
Calculates the Driver Trust Score (0 - 100) based on detected
commute events and optional rider feedback.

Transparent, rule-based, and explainable with human-readable evidence.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from ml.config import (
        INITIAL_TRUST_SCORE,
        MIN_TRUST_SCORE,
        MAX_TRUST_SCORE,
        WEIGHTS,
        MAX_PENALTIES_PER_EVENT_TYPE,
    )
except ImportError:
    from config import (
        INITIAL_TRUST_SCORE,
        MIN_TRUST_SCORE,
        MAX_TRUST_SCORE,
        WEIGHTS,
        MAX_PENALTIES_PER_EVENT_TYPE,
    )


def is_negative_feedback(feedback: Any) -> Tuple[bool, str]:
    """
    Evaluate rider feedback to determine if safety concerns were reported.

    Accepts:
    - Numeric rating: 1 or 2 stars (out of 5)
    - Dict: {"rating": 1, "comment": "..."} or {"safe": False, ...}
    - String: "poor", "bad", "unsafe", "scary", "rash", etc.

    Returns:
        (is_bad, reason_description)
    """
    if feedback is None:
        return False, ""

    if isinstance(feedback, (int, float)):
        if feedback <= 2:
            return True, f"Low rider rating received ({feedback}/5 stars)"
        return False, ""

    if isinstance(feedback, dict):
        if feedback.get("safe") is False:
            comment = feedback.get("comment", "Rider reported feeling unsafe")
            return True, f"Rider safety concern: {comment}"
        rating = feedback.get("rating")
        if isinstance(rating, (int, float)) and rating <= 2:
            comment = feedback.get("comment", "Poor rating")
            return True, f"Low rider rating ({rating}/5): {comment}"
        return False, ""

    if isinstance(feedback, str):
        negative_keywords = ["bad", "unsafe", "terrible", "poor", "danger", "scary", "rash", "harass"]
        lower = feedback.lower()
        if any(w in lower for w in negative_keywords):
            return True, f"Negative rider feedback: '{feedback}'"

    return False, ""


def compute_trust_score(events: List[Dict[str, Any]],
                        rider_feedback: Optional[Any] = None) -> Tuple[int, List[str]]:
    """
    Compute Driver Trust Score based on trip safety events and rider feedback.

    Starts at INITIAL_TRUST_SCORE (100).
    Applies penalties for detected incidents up to MAX_PENALTIES_PER_EVENT_TYPE.
    Awards CLEAN_TRIP_BONUS if no anomalies were detected.
    Ensures final score is clamped between MIN_TRUST_SCORE and MAX_TRUST_SCORE.

    Returns:
        (score: int, reasons: List[str])
    """
    score = INITIAL_TRUST_SCORE
    reasons: List[str] = []

    # Check rider feedback
    is_bad, feedback_reason = is_negative_feedback(rider_feedback)
    if is_bad:
        penalty = WEIGHTS.get("BAD_RIDER_FEEDBACK", -10)
        score += penalty
        reasons.append(f"{feedback_reason} ({penalty} pts)")

    # Group detected events by type
    events_by_type = defaultdict(list)
    for event in events:
        ev_type = event.get("type")
        if ev_type:
            events_by_type[ev_type].append(event)

    # If no safety events occurred and no bad feedback, apply clean trip bonus
    if not events and not is_bad:
        bonus = WEIGHTS.get("CLEAN_TRIP_BONUS", 2)
        score += bonus
        reasons.append(
            f"Clean commute verified: No route deviations, unauthorized stops, or GPS mismatch (+{bonus} pts)"
        )

    # Apply penalties for detected events with per-type capping
    for ev_type, event_list in events_by_type.items():
        weight = WEIGHTS.get(ev_type, -10)
        allowed_count = min(len(event_list), MAX_PENALTIES_PER_EVENT_TYPE)

        for i in range(allowed_count):
            ev = event_list[i]
            detail = ev.get("detail", f"{ev_type} detected")
            score += weight
            reasons.append(f"{detail} ({weight} pts)")

        if len(event_list) > MAX_PENALTIES_PER_EVENT_TYPE:
            reasons.append(
                f"Additional {len(event_list) - allowed_count} '{ev_type}' occurrences capped to prevent score distortion."
            )

    # Clamp score between 0 and 100
    final_score = int(round(max(MIN_TRUST_SCORE, min(MAX_TRUST_SCORE, score))))

    return final_score, reasons
