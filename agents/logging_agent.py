import os
import datetime as dt
from db.mock_db import log_session_mock
from db.firebase_db import save_session

# Checking firebase Key exists
USE_FIREBASE = os.path.exists("db/serviceAccountKey.json")

# Agent that log each exercise, either on Firebase or on a Mock_db (depends on the environment)
def log_session(
    exercise: str,
    sets: int,
    reps: int,
    weight_kg: float
):
    """
    Logs a completed set of a weightlifting exercise. This tool must be used
    immediately when the user provides all four required pieces of information:
    the exercise name, the number of sets, the repetitions, and the weight used.

    Args:
        exercise: The name of the exercise performed (e.g., 'Bench Press', 'Squat').
        sets: The total number of sets completed for this exercise (e.g., 4).
        reps: The number of repetitions per set (e.g., 12).
        weight_kg: The working weight used, measured in kilograms (kg), it can only have one decimal (e.g., 22.5).
    
    Returns:
        A success message indicating the data has been logged.
    """
    today = dt.date.today().isoformat()
    new_exercise = {
        "timestamp": dt.datetime.now().isoformat(),
        "exercise": exercise,
        "sets": sets,
        "reps": reps,
        "weight_kg": weight_kg,
    }
    if USE_FIREBASE:
        print("✅ Using FIREBASE DB...")
        results = save_session(today, new_exercise)
        return results 
    else:
        print("✅ Using Mock DB...")
        return log_session_mock(exercise, sets, reps, weight_kg)