import os
import json
from dotenv import load_dotenv
from db.mock_db import get_all_logs
import agents.memory_agent
import agents.summary_agent
import agents.coach_agent
import agents.logging_agent
import agents.evaluation_agent
import agents.stateful_agent
import agents.gymini_agent
from logs import log_event
import google.generativeai as genai

load_dotenv()
# Loading the GEMINI key
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')


# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)


CHAT_HISTORY = []


# Controller
def controller(user_input: str) -> str:
    text = agents.gymini_agent.ask_gymini(user_input).strip()

    # Remove the extra backticks to get a Raw JSON format.
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "")
    try:
        data = json.loads(text)

        # Controller: Logging Agent
        # Handles exercise logging requests. Extracts sets, reps, and weight,
        # routes them to the logging_agent, stores in the mock DB(works with firebase db as well but needs key), and returns confirmation.
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
        
        # Controller: Summary Agent
        # Retrieves all workout logs from the database, generates a raw summary,
        # then rewrites it into a motivational tone for the user.
        elif data.get("tool") == "get_summary":
            trace_id = log_event("Get Summary", "Fetching all workout logs")
            # This only will get data while working with mock_db
            data = get_all_logs()
            raw_summary = agents.summary_agent.get_summary(data)
            log_event("Summary Agent", f"Generated raw summary: {raw_summary}", trace_id)
            # Check if a name is saved in memory
            user_name = agents.memory_agent.get_name()
            if user_name:
                personalized_prompt = (
                    f"Rewrite this workout summary in a motivational tone, "
                    f"and address the user by name ({user_name}): {raw_summary}"
                )
            else:
                personalized_prompt = (
                    f"Rewrite this workout summary in a motivational tone: {raw_summary}"
                )
            return agents.gymini_agent.ask_gymini(personalized_prompt)

        # Controller: Memory Agent (Set Name)
        # Saves the user’s name into memory for personalization.
        # Confirms the save operation with logging events.
        elif data.get("tool") == "set_name":
            name = data.get("name")
            trace_id = log_event("Set Name", f"Name saved successfully: {name}")
            log_event("Memory Agent", f"Name saved successfully: {name}", trace_id)
            return agents.memory_agent.set_name(name)
        


        # Controller: Memory Agent (Get Name)
        # Retrieves the stored user name from memory_agent
        # and returns a personalized response.
        elif data.get("tool") == "get_name":
            trace_id = log_event("Get Name", "Retrieving stored name")
            raw = agents.memory_agent.get_name()
            log_event("Memory Agent", f"Retrieved name: {raw}", trace_id)
            return personalize_response(raw)
        
        # Controller: Coach Agent
        # Provides exercise tips. Delegates to ask_coach() for raw results,
        # parses JSON, and if needed, calls search_web via coach_tools.
        # Final tips are rewritten into a supportive, coach-like tone.   
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
                return agents.gymini_agent.ask_gymini(results)
            
        # Controller: Evaluation Agent
        # Runs evaluation across all agents using EvaluationAgent.
        # Summarizes results and rewrites them into a user-friendly report.
        elif data.get("tool") == "evaluate_agents":
            evaluator = agents.evaluation_agent.EvaluationAgent()
            results = evaluator.run_all()
            log_event("Evaluation Agent", f"Completed evaluation: {results}")
            return agents.gymini_agent.ask_gymini(f"Report these evaluation results to the user: {results}")
        
        
        # Controller: Help user
        # Responds to user who needs help about Gymini's functions.
        elif data.get("tool") == "help":
            return agents.gymini_agent.ask_gymini(
        "Explain your features in a friendly way. \
        Mention logging workouts, summaries, coaching tips, memory, and evaluation. \
        leave evaluation out. Keep it warm, simple, and focused on the gym ritual."
    )
        # Controller: Creator Signature
        # Responds to identity queries ("who made you") with a fixed signature line.
        elif data.get("tool") == "get_creator":
            return "I was made with ❤️ by Aymen Kalaï Ezar."

    except Exception:
        # Friendly fallback: explain Gymini's abilities
        print("This is the fallback agent...")
        return agents.gymini_agent.ask_gymini(
            f"Analyze user input ({text}) and suggest the closest feature Gymini can perform. "
            f"Available features: log workouts, workout summaries, coaching tips, memory (name). "
            f"IMPORTANT: Do NOT mention tools or functions."
            f"List each feature as a bullet point starting with '-' and keep the tone friendly."
    )
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

    smart_chat_loop()

if __name__ == "__main__":
    main()
