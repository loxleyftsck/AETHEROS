"""
LLM Configuration Module
Provides the globally configured LLM instance for all LangGraph and CrewAI Agents.
Set up specifically for Local NVIDIA RTX 3050 execution via Ollama.
"""
import os
import structlog
from langchain_community.llms import Ollama

logger = structlog.get_logger()

# For a 4GB-8GB VRAM RTX 3050, the recommended model is Llama 3 (8B) quantized or Phi-3
# Ollama natively handles GPU offloading if installed correctly on Windows.
LOCAL_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_llm():
    """
    Returns the configured LLM backbone.
    Defaults to computationally free, GPU-accelerated local Ollama.
    """
    logger.info("Initializing Local GPU LLM", model=LOCAL_MODEL, url=OLLAMA_URL)
    
    # We increase the context window and timeout for complex CrewAI reasoning
    return Ollama(
        model=LOCAL_MODEL,
        base_url=OLLAMA_URL,
        temperature=0.3, # Keep low for deterministic financial reasoning
        timeout=120,    # Local inference can take a bit longer on 3050 under heavy load
    )
