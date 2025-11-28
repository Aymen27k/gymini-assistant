import datetime as dt
import time
import google.generativeai as genai
import agents.memory_agent
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable, DeadlineExceeded


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
        # Evaluation tools
        - If the user ask to run an evaluation or evaluate all the agents.
        respond ONLY with:
        {{
        "tool": "evaluate_agents"
        }}
        If the user asks "who made you", "who created you", or similar,
        respond ONLY with:
        {{"tool": "get_creator"}}
        If the user asks "what can you do", or similar,
        respond ONLY with:
        {{"tool": "help"}}                                      
                                                                                    
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
        return response.replace("Hey there", f"Hey {name}")
    return response
