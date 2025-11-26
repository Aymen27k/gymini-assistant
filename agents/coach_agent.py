import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests

load_dotenv()
# Loading the GEMINI key
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')


API_KEY = os.getenv("gymini-search-key")
CX = "d5cf4b299c6f14de3"

def search_web_impl(query: str):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": API_KEY,
        "cx": CX,
        "num": 5
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def format_tips(results, exercise: str) -> str:
    items = results.get("items", [])
    if not items:
        return f"No tips found for {exercise}."

    formatted = f"🏋️ Tips for {exercise}:\n"
    for item in items[:3]:
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        formatted += f"- {snippet} ({link})\n"
    #print(f"FORMATTED TIPS : {formatted}")
    return formatted


def coach_tools(exercise: str):
    query = f"{exercise} exercise tips best practices"
    results = search_web_impl(query)
    return format_tips(results, exercise)

def ask_coach(user_input: str):
    #print(f"Data inside ASK_COACH : {user_input}")
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(f"""
    You are Coach Agent.
    When asked to call a tool, respond ONLY with a raw JSON object. Do not use backticks or code fences."                                       
    If the user asks for exercise tips, respond ONLY with:
    {{
      "tool": "search_web",
      "query": "<exercise_name>"
    }}
    Do not provide explanations, text, or code fences. Output only the JSON.
    User: {user_input}
    """)
    return response.text
