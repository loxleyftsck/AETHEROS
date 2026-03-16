"""
The Central Manager that delegates and runs the CrewAI Research Mesh.
"""
from crewai import Task, Crew, Process
from .market_analyst import create_market_analyst
from .sentiment_spy import create_sentiment_spy
from .macro_scout import create_macro_scout

import os
# LLM configuration via environment variables
os.environ["OPENAI_API_KEY"] = "sk-placeholder" # Will be set via UI or ENV

def run_research_mesh(symbol: str) -> str:
    """
    Executes the 3-Agent CrewAI mesh to generate a unified market context for the given symbol.
    """
    # Instantiate Agents
    analyst = create_market_analyst()
    spy = create_sentiment_spy()
    scout = create_macro_scout()
    
    # Define Specific Tasks
    tech_task = Task(
        description=f"Fetch the moving averages and price history for {symbol}. Output a strict mathematical breakdown of the current trend.",
        expected_output="A structured summary containing the current price, SMA20, SMA50, and a Bullish/Bearish conclusion.",
        agent=analyst
    )
    
    social_task = Task(
        description=f"Search the web for the latest news and retail sentiment regarding {symbol}. Is the crowd greedy or fearful?",
        expected_output="A 2-paragraph summary of the current social/news hype, concluding with an overall sentiment score (Greed vs Fear).",
        agent=spy
    )
    
    macro_task = Task(
        description=f"Check the broader global economic news. Are there rising interest rates, global conflicts, or massive crashes? Determine if the environment is safe to trade {symbol} today.",
        expected_output="A brief macro-economic status report indicating 'SAFE', 'CAUTION', or 'DANGER' for the overall market.",
        agent=scout
    )
    
    # Form the Crew
    # We use a hierarchical process where a manager (automatically created by CrewAI) oversees the 3 agents,
    # or a Sequential process where they run one after another. Since we want independent research, sequential is fine for Phase 3.
    research_crew = Crew(
        agents=[scout, analyst, spy],
        tasks=[macro_task, tech_task, social_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Kickoff the multi-agent execution
    result = research_crew.kickoff()
    return result
