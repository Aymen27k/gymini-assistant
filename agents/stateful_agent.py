import google.generativeai as genai


def ask_main_agent_with_history(user_input: str, history: list[dict]) -> str:
    """
    Calls the main agent model, passing the entire chat history for context.
    Ensures pronouns or vague references are resolved using past conversation.
    Returns ONLY a raw JSON object.
    """
    # Exceptions to passthrough to ask_gymini() LLM 
    lowered = user_input.lower()
    if "my name is" in lowered or "what is my name" in lowered or "do you know my name" in lowered:
        # return the raw prompt unchanged ask_gymini can handle it.
        return user_input
    if "who made you" in lowered or "who created you" in lowered:
      return user_input
    if "what can you do" in lowered or "help" in lowered:
      return user_input
    
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    # Build the conversation history string
    history_text = ""
    for msg in history:
        role = msg.get("role", "user")
        parts = " ".join(part.get("text", "") for part in msg.get("parts", []))
        history_text += f"{role.capitalize()}: {parts}\n"
    
    response = model.generate_content(f"""
    You are the Gymini Assistant.
    Your sole job is to analyze the conversation history and the latest user message
    to determine the appropriate tool command.

    Rules:
    - ONLY output a raw JSON object.
    - Do not use backticks or code fences.
    - Use the history to resolve pronouns or missing context
      (e.g., 'it', 'them' refers to the last mentioned exercise).

    Conversation History:
    {history_text}

    User: {user_input}
    """)
    return response.text.strip()
