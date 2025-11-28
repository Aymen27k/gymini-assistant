import os
import datetime as dt
import json
from dotenv import load_dotenv
from db.mock_db import get_all_logs
import agents.memory_agent
import agents.summary_agent
import agents.coach_agent
import agents.logging_agent
import agents.evaluation_agent
import agents.stateful_agent
from logs import log_event
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

CHAT_HISTORY = []

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
            exercise = data["exercise"]
            sets = data["sets"]
            reps = data["reps"]
            weight = data["weight_kg"]
            trace_id = log_event("Log Session", f"Routing to logging_agent with {sets}×{reps} {exercise} at {weight}kg")

            # Call the agent
            results = agents.logging_agent.log_session(exercise, sets, reps, weight)
            print(f"Results after calling the agent : {results}")
            log_event("Logging Agent", f"Exercise logged successfully (ID: {results['id']})", trace_id)
            return results["message"]
        elif data.get("tool") == "get_summary":
            trace_id = log_event("Get Summary", "Fetching all workout logs")
            data = get_all_logs()
            raw_summary = agents.summary_agent.get_summary(data)
            log_event("Summary Agent", f"Generated raw summary: {raw_summary}", trace_id)
            return ask_gymini(
                f"Rewrite this workout summary in a motivational tone: {raw_summary}"
            )
        elif data.get("tool") == "set_name":
            name = data.get("name")
            trace_id = log_event("Set Name", f"Name saved successfully: {name}")
            log_event("Memory Agent", f"Name saved successfully: {name}", trace_id)
            return agents.memory_agent.set_name(name)
        elif data.get("tool") == "get_name":
            trace_id = log_event("Get Name", "Retrieving stored name")
            raw = agents.memory_agent.get_name()
            log_event("Memory Agent", f"Retrieved name: {raw}", trace_id)
            return personalize_response(raw)
        
        elif data.get("tool") == "coach_agent":
            exercise = data.get("exercise")
            trace_id = log_event("Coach Agent", f"Received exercise input: {exercise}")

            response_text = agents.coach_agent.ask_coach(exercise)
            log_event("Coach Agent", f"Raw response from ask_coach: {response_text}", trace_id)
            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError:
                log_event("Coach Agent", "Error: response was not valid JSON", trace_id)
                return None
            # Now check the tool field
            if response_json.get("tool") == "search_web":

                query = response_json.get("query")
                log_event("Coach Agent", f"Delegating to search_web with query: {query}", trace_id)
                results = agents.coach_agent.coach_tools(query)
                log_event("Coach Agent", f"Final results from coach_tools: {results}", trace_id)
                log_event("Coach Agent", "Delivered motivational confirmation to user", trace_id)
                return ask_gymini(results)
        elif data.get("tool") == "evaluate_agents":
            evaluator = agents.evaluation_agent.EvaluationAgent()
            results = evaluator.run_all()
            log_event("Evaluation Agent", f"Completed evaluation: {results}")
            return ask_gymini(f"Report these evaluation results to the user: {results}")
        elif data.get("tool") == "get_creator":
            return "I was made with ❤️ by Aymen Kalaï Ezar."

    except Exception:
        # fallback: just return Gymini's text
        print("This is the fallback output...")
        return text

# The Chatbot logic
def smart_chat_loop():
    global CHAT_HISTORY
    print("🤖 Gymini is ready! Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Gymini: Goodbye! Keep training strong 💪")
            break

        # 1. Ask the main agent with history
        raw_json_response = agents.stateful_agent.ask_main_agent_with_history(user_input, CHAT_HISTORY)
        
        # 2. Process JSON through controller
        final_response = controller(raw_json_response)

        # 3. Update history
        CHAT_HISTORY.append({"role": "user", "parts": [{"text": user_input}]})
        CHAT_HISTORY.append({"role": "model", "parts": [{"text": final_response}]})

        # 4. Print response
        print(f"Gymini: {final_response}")

def main():
    #controller("I did 4 sets of 5 reps of Squats at 30 kilos.")
    #controller("I did 3 sets of 6 reps of Bench Press at 22.5 kilos.")

    """ data = get_all_logs()
    summary = agents.summary_agent.get_summary(data)
    polished_summary = ask_gymini(f"Rewrite this workout summary in a friendly, motivational tone: {summary}")
    print(polished_summary) """

    smart_chat_loop()

if __name__ == "__main__":
    main()
