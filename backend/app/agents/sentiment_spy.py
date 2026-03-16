"""
The Social Sentiment Analyst Profile.
"""
from crewai import Agent
from .tools.search_tools import search_news
# For Phase 3, we mock intensive Reddit/Twitter parsing with general web search due to API limits.
# In production, PRAW or X API would plug in here.

def create_sentiment_spy() -> Agent:
    """
    Instantiates the Sentiment Spy Agent.
    Focuses on measuring retail hype, fear, and market rumors.
    """
    return Agent(
        role="Retail Sentiment Analyst & Social Media Spy",
        goal="Discover what the retail crowd and news media are currently saying about {symbol}. Gauge the greed or fear level.",
        backstory=(
            "You are a behavioral economist specializing in herd psychology. "
            "You don't care about moving averages or cash flow statements. "
            "You care about the hype. Are people euphoric? Are they panicking? "
            "Your job is to read news headlines and summarize if the public sentiment is overwhelmingly Bullish, Bearish, or Neutral."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[search_news]
    )
