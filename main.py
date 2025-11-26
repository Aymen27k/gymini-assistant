import os
import datetime as dt
import json
from dotenv import load_dotenv
from db.firebase_init import initialize_firebase
from db.mock_db import log_session_mock, get_all_logs
import agents.memory_agent
import agents.summary_agent
import agents.coach_agent
from firebase_admin import firestore
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded

# Checking firebase Key exists

USE_FIREBASE = os.path.exists("db/serviceAccountKey11.json")



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
        - If the user asks for a workout summary (e.g., "Give me my last session summary"),
        respond ONLY with a JSON object in this format:
        {{
            "tool": "get_summary"
        }}
                                              
        # Coach Agent
        If the user asks for exercise tips, respond ONLY with a JSON object in this format:
        {{
            "tool": "coach_agent",
            "exercise": "<exercise_name>"
        }}
        # Coach Agent Formatter
        If you are given raw search results (snippets + links) from the coach_agent,
        rewrite them into a clear, user-friendly coaching response.

        Guidelines:
        - Summarize into 3–5 actionable tips.
        - Use a numbered or bulleted list.
        - Keep each tip short, practical, and motivational.
        - Preserve source links at the end of each tip.
        - Speak in a supportive, coach-like tone.
        - Begin with: "🏋️ Tips for <exercise_name>:"
                                                     
        # Memory tools                                      
        - If the user introduces themselves (e.g., "my name is <X>", "call me <X>"),
        respond ONLY with this JSON object:
        {{
        "tool": "set_name",
        "name": "<X>"
        }}
        - If the user asks to recall their identity (e.g., "what is my name?", "do you remember my name?"),
        respond ONLY with:
        {{
        "tool": "get_name"
        }}                                                                      
        Otherwise, answer normally.
        User: {user_input}
        """)
            raw_text = response.text
            return personalize_response(raw_text)
        except (ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
            delay *= backoff
            attempt += 1
    return "Gymini couldn't respond after multiple attempts. Please try again later."

# A wrapper function for Gymini LLM to make the response more personalized
def personalize_response(response) -> str:
    data = agents.memory_agent.get_name()
    name = data.get("user_name") if isinstance(data, dict) else data
    if name and response.strip().lower() == name.lower():
        return f"Hey {name}, I remember your name."
    if name:
        return response.replace("Hey", f"Hey {name}")
    return response

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
        elif data.get("tool") == "get_summary":
            data = get_all_logs()
            raw_summary = agents.summary_agent.get_summary(data)
            return ask_gymini(
                f"Rewrite this workout summary in a motivational tone: {raw_summary}"
            )
        elif data.get("tool") == "set_name":
            name = data.get("name")
            return agents.memory_agent.set_name(name)
        elif data.get("tool") == "get_name":
            raw = agents.memory_agent.get_name()
            return personalize_response(raw)
        
        elif data.get("tool") == "coach_agent":
            #print("I am inside coach agent controller")
            exercise = data.get("exercise")
            response_text = agents.coach_agent.ask_coach(exercise)
            #print(f"This is the response_text from ask_coach : {response_text}")
            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError:
                print("Error: response was not valid JSON")
                return None
            # Now check the tool field
            if response_json.get("tool") == "search_web":
                #print("I am inside search web controller")
                query = response_json.get("query")
                results = agents.coach_agent.coach_tools(query)
                #print(f"Final results : {results}")
                return ask_gymini(results)

    except Exception:
        # fallback: just return Gymini's text
        print("This is the fallback output...")
        return text

# The Chatbot logic 
def chat_loop():
    print("🤖 Gymini is ready! Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            print("Gymini: Goodbye! Keep training strong 💪")
            break
        response = controller(user_input)
        print(f"Gymini: {response}")

def main():
    #controller("I did 4 sets of 5 reps of Squats at 30 kilos.")
    #controller("I did 3 sets of 6 reps of Bench Press at 22.5 kilos.")

    """ data = get_all_logs()
    summary = agents.summary_agent.get_summary(data)
    polished_summary = ask_gymini(f"Rewrite this workout summary in a friendly, motivational tone: {summary}")
    print(polished_summary) """

    chat_loop()

if __name__ == "__main__":
    main()
