"""
Social Sentiment Tools for the SentimentSpy Agent
"""
from langchain_community.tools import tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

@tool("Search_Internet_For_News")
def search_news(query: str) -> str:
    """
    Search the internet for the most recent news articles related to a stock/crypto.
    Args:
        query (str): The search term, e.g., "Apple stock news" or "Bitcoin ETF updates".
    Returns:
        List of summarized top news headlines.
    """
    try:
        search = DuckDuckGoSearchAPIWrapper()
        results = search.run(query)
        if not results:
            return "No recent news found."
        return results
    except Exception as e:
        return f"Error fetching news: {str(e)}"
