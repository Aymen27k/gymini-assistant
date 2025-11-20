import datetime as dt
import uuid

# This is our mock database: a simple list in memory.
WORKOUT_LOGS = {}

def log_session_mock(exercise: str, sets: int, reps: int, weight_kg: float) -> str:
    """
    Simulates logging a workout session to a database.
    Instead of writing to Firestore, it appends the data to a Python list.
    """
    # Generate a mock document ID
    mock_id = str(uuid.uuid4())[:8]
    # Date of today
    today = dt.date.today().isoformat()
    # Preparing exercise details
    new_exercise = {
        "id": mock_id,
        "exercise": exercise,
        "sets": sets,
        "reps": reps,
        "weight_kg": weight_kg,
        "timestamp": dt.datetime.now().isoformat(),
        "date_string": dt.date.today().isoformat(),
        "user_id": "mock_reviewer" # Use a consistent ID for testing
    }

    # Check if this is the first log of the day
    if today not in WORKOUT_LOGS:
        WORKOUT_LOGS[today] = {"date": today, "exercises": []}

    # "Write" the data to the mock database
    WORKOUT_LOGS[today]["exercises"].append(new_exercise)

    # Print the log locally for the reviewer to verify it was "saved"
    print("\n--- MOCK DB LOGGED DATA ---")
    print(f"Logged: {WORKOUT_LOGS}")
    print(f"Total Logs in Mock DB: {len(WORKOUT_LOGS)}")
    print("---------------------------\n")

    # Return a success message formatted like the real Firestore success message
    return f"✅ Success! Logged {sets} sets of {reps} reps of {exercise} at {weight_kg}kg to Mock DB. (ID: {mock_id})"

def get_all_logs():
    """Returns the entire mock database list for debugging/verification."""
    return WORKOUT_LOGS