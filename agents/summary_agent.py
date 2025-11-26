import db.mock_db


def get_summary(mock_db, last_session=True):
    # Step 1: Find the latest session (last date key)
    last_date = max(mock_db.keys())  # e.g. "2025-11-20"
    session = mock_db[last_date]

    # Step 2: Extract exercises
    exercises = session["exercises"]

    # Step 3: Build summary string
    summary_parts = []
    for ex in exercises:
        # Format float cleanly: 30.0 → 30, 22.5 → 22.5
        weight = int(ex["weight_kg"]) if ex["weight_kg"].is_integer() else ex["weight_kg"]
        summary_parts.append(
            f"{ex['sets']}×{ex['reps']} {ex['exercise']} at {weight}kg"
        )

    # Step 4: Return natural summary
    return f"On {last_date}, you did " + " and ".join(summary_parts) + "."

