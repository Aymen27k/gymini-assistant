import os
import datetime as dt
from firebase_admin import firestore
from db.firebase_init import initialize_firebase
from db.mock_db import log_session_mock

# Checking firebase Key exists
USE_FIREBASE = os.path.exists("db/serviceAccountKey11.json")


# Loading the firebase db
db = initialize_firebase()

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
    if USE_FIREBASE:
        print("✅ Using FIREBASE DB...")
        db = firestore.client()
        doc_ref = db.collection("sessions").document(today)
        new_exercise = {
            "timestamp": dt.datetime.now().isoformat(),
            "exercise": exercise,
            "sets": sets,
            "reps": reps,
            "weight_kg": weight_kg,
        }
        doc_ref.set({
            "date": today,
            "exercises": firestore.ArrayUnion([new_exercise])
        }, merge=True)
        # We will add the actual Firebase logging logic here later.
        print(f"✅ Successfully logged {sets} sets of {reps} reps of {exercise} at {weight_kg}kg.")
    else:
        print("✅ Using Mock DB...")
        return log_session_mock(exercise, sets, reps, weight_kg)