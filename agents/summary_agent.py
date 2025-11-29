import db.mock_db
from db.firebase_db import get_last_session
import datetime as dt


def get_summary(last_session=True) -> dict:
    """
    Summarize the latest workout session from Firebase.
    Returns a dict with id + message for consistency.
    """
    session = get_last_session()
    if not session:
        return {"id": "summary", "message": "No workouts logged yet."}

    date = session["date"]
    exercises = session.get("exercises", [])

    if not exercises:
        return {"id": "summary", "message": f"No exercises logged for {date}."}

    summary_parts = []
    for ex in exercises:
        weight = int(ex["weight_kg"]) if float(ex["weight_kg"]).is_integer() else ex["weight_kg"]
        summary_parts.append(f"{ex['sets']}×{ex['reps']} {ex['exercise']} at {weight}kg")

    return {
        "id": "summary",
        "message": f"On {date}, you did " + " and ".join(summary_parts) + "."
    }
