"""
YFinance Technical Analysis Tools for the MarketAnalyst Agent
"""
from langchain_community.tools import tool
import yfinance as yf
import pandas as pd
import json

@tool("Get_Stock_Price_And_History")
def get_stock_history(symbol: str, period: str = "1mo", interval: str = "1d") -> str:
    """
    Fetches the historical price data for a given stock or crypto ticker.
    Args:
        symbol (str): The ticker symbol (e.g., 'AAPL', 'BTC-USD').
        period (str): The time period to fetch (e.g., '1d', '5d', '1mo', '3mo', '1y').
        interval (str): The frequency of data (e.g., '1m', '1h', '1d', '1wk').
    Returns:
        JSON string of the most recent price records.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return f"No data found for symbol: {symbol}"
            
        # Return only the last 5 rows to save LLM context
        recent = df.tail(5)
        # Convert index to string for JSON serialization
        recent.index = recent.index.astype(str)
        return recent.to_json(orient='index')
    except Exception as e:
        return f"Error fetching data: {str(e)}"

@tool("Get_Moving_Averages")
def get_moving_averages(symbol: str) -> str:
    """
    Calculates the 20-day and 50-day Simple Moving Averages (SMA) to determine the trend.
    Args:
        symbol (str): The ticker symbol.
    Returns:
        JSON string indicating current price, SMA20, SMA50, and the Trend (Bullish/Bearish).
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo")
        if df.empty:
            return f"No data found for symbol: {symbol}"
            
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        latest = df.iloc[-1]
        
        trend = "Bullish" if latest['SMA_20'] > latest['SMA_50'] else "Bearish"
        
        res = {
            "Symbol": symbol,
            "Current_Price": round(latest['Close'], 2),
            "SMA_20": round(latest['SMA_20'], 2),
            "SMA_50": round(latest['SMA_50'], 2),
            "Trend_Indicator": trend
        }
        return json.dumps(res)
    except Exception as e:
        return f"Error calculating moving averages: {str(e)}"
