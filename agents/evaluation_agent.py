import json
import agents.logging_agent
import agents.coach_agent

class EvaluationAgent:
  
    def evaluate_log_session(self):
        result = agents.logging_agent.log_session("squats", 3, 10, 50.0)
        assert isinstance(result, dict), "Expected dict return"
        assert "message" in result, "Missing success message"
        return "log_session passed ✅"

    def evaluate_coach_agent(self):
        response = agents.coach_agent.ask_coach("squats")
        try:
            json.loads(response)
            return "coach_agent passed ✅"
        except json.JSONDecodeError:
            return "coach_agent failed ❌"

    def run_all(self):
        return {
            "log_session": self.evaluate_log_session(),
            "coach_agent": self.evaluate_coach_agent(),
            # add more evaluations here
        }
if __name__ == "__main__":
    evaluator = EvaluationAgent()
    results = evaluator.run_all()
    print("Evaluation Results:")
    for agent, status in results.items():
        print(f"- {agent}: {status}")
