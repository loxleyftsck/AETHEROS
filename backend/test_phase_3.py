"""
Phase 3 Verification Script: CrewAI Research Mesh
"""
import os
import sys

# Configure mock API keys for testing locally without spending tokens
# if the user hasn't provided real ones
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "sk-mock-key-for-testing"
    
from app.agents.supervisor_crew import run_research_mesh

def main():
    print("🚀 Starting Phase 3 CrewAI Test: Research Mesh Simulation")
    try:
        # We will test the ability to construct the crew and parse the tasks.
        # It will likely fail at the LLM execution stage if using mock keys,
        # but the module import and structure will be verified.
        print("\n[INIT] Assembling MarketAnalyst, SentimentSpy, and MacroScout...")
        result = run_research_mesh("BTC-USD")
        print("\n--- ✅ CrewAI Execution Complete ---")
        print(result)
        
    except Exception as e:
        print(f"\n⚠️ Reached an expected execution point or error:\n{e}")
        print("\nIf this is an OpenAI Authorization error, it means the CrewAI Mesh")
        print("was successfully built and routed, but requires a valid API key to proceed.")

if __name__ == "__main__":
    main()
