import os
import datetime as dt
import json
from dotenv import load_dotenv
from db.firebase_init import initialize_firebase
from db.mock_db import log_session_mock, get_all_logs
from firebase_admin import firestore
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded

# Checking firebase Key exists

USE_FIREBASE = os.path.exists("db/serviceAccountKey.json")



load_dotenv()
# Loading the GEMINI key
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

# Loading the firebase db
db = initialize_firebase()

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Define Gymini's persona
persona = """
You are Gymini, an AI workout assistant.
Your role is to log exercises, suggest routines, and provide coaching tips.
Always be concise, supportive, and context-aware.
"""

# Gymini LLM model
def ask_gymini(user_input: str, max_attempts=5, delay=1, backoff=2)-> str:
    attempt = 0
    while attempt < max_attempts:
        try:
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(f"""
        You are Gymini. If the user provides workout details (exercise, sets, reps, weight),
        respond ONLY with a JSON object in this format:
        {{
          "tool": "log_session",
          "exercise": "<name>",
          "sets": <int>,
          "reps": <int>,
          "weight_kg": <float>
        }}
        Otherwise, answer normally.
        User: {user_input}
        """)
            return response.text
        except (ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
            delay *= backoff
            attempt += 1
    return "Gymini couldn't respond after multiple attempts. Please try again later."

# Agent that log each exercise, either on Firebase or on a Mock_db (depends on the environment)
def log_session(
    exercise: str,
    sets: int,
    reps: int,
    weight_kg: float
) -> str:
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


# Controller
def controller(user_input: str) -> str:
    text = ask_gymini(user_input).strip()
    #print("Raw Gymini output:", text)

    # Remove the extra backticks to get a Raw JSON format.
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "")
    try:
        data = json.loads(text)
        if data.get("tool") == "log_session":
            return log_session(
                data["exercise"],
                data["sets"],
                data["reps"],
                data["weight_kg"]
            )
    except Exception:
        # fallback: just return Gymini's text
        return text

def main():
    controller("I did 4 sets of 5 reps of Squats at 30 kilos.")
    controller("I did 3 sets of 6 reps of Bench Press at 22.5 kilos.")
    print(get_all_logs())




if __name__ == "__main__":
    main()