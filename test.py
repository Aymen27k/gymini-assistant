# adk_wrapper.py
from main import controller

# ADK expects a run() function
def run(input_text: str) -> dict:
    result = controller(input_text)
    # Adapt Gymini’s output to ADK schema
    return {
        "tool": result["tool"],
        "exercise": result["exercise"],
        "sets": result["sets"],
        "reps": result["reps"],
        "weight_kg": result["weight_kg"]
    }

controller("I did 4 sets of 8 reps of Squats at 120 kilos.")