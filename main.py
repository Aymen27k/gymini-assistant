import os
import time
from dotenv import load_dotenv
#from google import genai, types
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded




load_dotenv()
# Loading the GEMINI key
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')


# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Define Gymini's persona
persona = """
You are Gymini, an AI workout assistant.
Your role is to log exercises, suggest routines, and provide coaching tips.
Always be concise, supportive, and context-aware.
"""




def log_session(
    exercise: str,
    sets: int,
    reps: int,
    weight_kg: int
) -> str:
    """
    Logs a completed set of a weightlifting exercise. This tool must be used
    immediately when the user provides all four required pieces of information:
    the exercise name, the number of sets, the repetitions, and the weight used.

    Args:
        exercise: The name of the exercise performed (e.g., 'Bench Press', 'Squat').
        sets: The total number of sets completed for this exercise (e.g., 4).
        reps: The number of repetitions per set (e.g., 12).
        weight_kg: The working weight used, measured in kilograms (kg) (e.g., 80).
    
    Returns:
        A success message indicating the data has been logged.
    """
    
    # NOTE: We will add the actual Firebase logging logic here later.
    return f"Successfully logged {sets} sets of {reps} reps of {exercise} at {weight_kg}kg."

# Gymini LLM model
def ask_gymini(user_input: str, max_attempts=5, delay=1, backoff=2)-> str:
    attempt = 0
    while attempt < max_attempts:
        try:
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            response = model.generate_content(user_input)
            return response.text
        except (ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
            delay *= backoff
            attempt += 1
    return "Gymini couldn't respond after multiple attempts. Please try again later."
def main():
    pass


if __name__ == "__main__":
    main()