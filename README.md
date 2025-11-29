# gymini-assistant

Gymini helps you train smarter by logging workouts, providing personalized summaries of your progress, and offering real-time coaching tips.

It's a friendly workout companion that helps you log workouts, track progress, get coaching tips, and personalize your fitness journey. Built with modular agents, it’s designed for both users and reviewers to experience a polished, resilient assistant.

### What I Created

Gymini is a **multi-agent ecosystem** designed to assist during workout sessions. Its architecture includes:

- **Logger Agent:** records sets, reps, and weights in natural conversation.
- **Context Manager:** remembers which exercise is active across turns.
- **Coach Agent:** fetches technique tips and safety cues.
- **Data Guardian:** validates inputs and filters inappropriate entries.
- **Summarizer Agent:** recaps sessions and tracks progress over time.

Each agent is modular and composable, allowing clean chaining and easy debugging. The system is designed to feel like a real training partner — attentive, helpful, and never intrusive.

### Demo Flow

Gymini responds naturally to workout phrases in a fluid sequence:

- **User:** "Log 3 sets of 10 at 80kg for Bench Press."
- **Gymini:** Confirms the workout was logged successfully.
- **User:** "Now I’m doing Squats."
- **Gymini:** Switches the active exercise context.
- **User:** "Give me a tip for Deadlifts."
- **Gymini:** Provides relevant safety and technique cues.
- **User:** "Summarize today’s workout."
- **Gymini:** Delivers a personalized recap of the session.

### Installation

Clone the repository and install dependencies:
git clone https://github.com/Aymen27k/gymini-assistant
cd gymini-assistant
pip install -r requirements.txt
python main.py

### Requirements

Gymini requires API keys to function properly:

- **GOOGLE_API_KEY** → Needed for the LLM to process natural language and conversation.
- **GOOGLE_CLOUD_API_KEY** → Required by the Coach Agent to fetch live coaching tips online.

### Design Decisions

- **Generative AI vs ADK:**  
  I chose Generative AI instead of the ADK to prototype natural conversation quickly and give Gymini a more human‑like coaching style. This allowed me to focus on modular agent flows and JSON‑based communication without heavy boilerplate. ADK could be useful for production deployment, but Generative AI provided the speed and flexibility needed for this project.

- **Persistence & Memory (Firebase vs Mock DB):**  
  Gymini reached the stage where workout data could be saved to a Firebase Cloud Database, proving the feasibility of long‑term memory and persistence across sessions.  
  However, I chose to continue with a mock database for this submission due to uncertainty around securely handling the required JSON key. This ensured stability and simplicity during evaluation, while leaving a clear path for future Firebase integration and server deployment.

- **Separation of Concerns (Agent Architecture):**  
  Each agent was built as a standalone module inside the `agents/` folder, with a clear single responsibility:
  - `logging_agent.py` → Handles workout logging.
  - `stateful_agent.py` → Tracks active exercise context.
  - `coach_agent.py` → Provides technique and safety tips.
  - `summary_agent.py` → Generates session recaps.
  - `evaluation_agent.py` → Reserved for future agent evaluation logic.
  - `gymini_agent.py` → Orchestrates agent flows and user interaction.
- **Modular Database Layer:**  
  The `db/` folder contains both `mock_db.py` for local testing and `firebase_init.py` for cloud persistence.
- **Main Entry Point & Routing:**  
  `main.py` serves as the orchestrator, importing agents, managing the chat loop, and routing user input to the correct agent.  
  This keeps the core logic centralized while preserving modularity.
  - **Security & Key Management:**  
    Sensitive files such as `.env` and `serviceAccountKey.json` are intentionally excluded from the repository using `.gitignore`.  
    This ensures secure handling of API credentials while allowing reviewers to inspect the Firebase integration logic in `firebase_init.py`.
