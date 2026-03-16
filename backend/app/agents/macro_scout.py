"""
The Macro Economics Scout Profile.
"""
from crewai import Agent
from .tools.search_tools import search_news

def create_macro_scout() -> Agent:
    """
    Instantiates the Macro Scout Agent.
    Checks the "weather" of the broader market (Federal Reserve, Crypto Global Market Cap, etc.)
    """
    return Agent(
        role="Global Macro Economist",
        goal="Determine if the global macroeconomic environment is safe for investing in {symbol} today.",
        backstory=(
            "You see the forest, not the trees. You monitor interest rates, global conflict, and massive market-wide shifts. "
            "If the US Federal Reserve raises rates, or if the broader market crashes, you warn the other agents not to buy, "
            "regardless of how good the technicals look. You act as the first line of defense."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[search_news]
    )
