"""
LangGraph Processing Nodes
Includes SignalForge (LLM Synthesis) and RiskGuard (Rust FFI calls).
"""
import structlog
import json
from .state import GoldmineState
from app.core.llm_config import get_llm
from goldmine_core import TopKMemory, HftRulesEngine # The compiled PyO3 Rust Engine

logger = structlog.get_logger()

def signal_forge_node(state: GoldmineState) -> GoldmineState:
    """
    Reads the CrewAI research context and uses a strict LLM prompt
    to convert the prose into a structured trading JSON signal.
    """
    logger.info("Running SignalForge Node", symbol=state["symbol"])
    
    if not state.get("research_context"):
        state["errors"].append("Missing research context")
        state["is_terminal"] = True
        return state
        
    llm = get_llm()
    
    prompt = f"""
    You are an autonomous algorithmic trading signal generator.
    Review the following multi-agent research report for '{state['symbol']}':
    {state['research_context']}
    
    Extract the overall sentiment and output STRICTLY ONE valid JSON object with the following keys:
    - "direction": "long" or "short" or "neutral"
    - "confidence": A float between 0.0 and 1.0
    - "rr": Estimated Risk/Reward ratio float (e.g. 1.5, 2.0)
    - "fear_index": A float from 0 to 100 based on macro sentiment.
    
    JSON Output:
    """
    
    try:
        response = llm.invoke(prompt)
        # Attempt to parse json from text (handling markdown wrappers if LLM adds any)
        clean_json = response.replace("```json", "").replace("```", "").strip()
        signal = json.loads(clean_json)
        state["proposed_signal"] = signal
    except Exception as e:
        logger.error("SignalForge failed to parse LLM JSON", err=str(e))
        state["errors"].append("Invalid JSON from LLM Synthesis")
        state["is_terminal"] = True
        
    return state

def risk_guard_node(state: GoldmineState) -> GoldmineState:
    """
    Calls the native Rust HFT engine to run high-speed checks on the 
    hallucination/confidence mathematics of the proposed signal.
    """
    logger.info("Running RiskGuard Node (Rust Engine Checkout)", symbol=state["symbol"])
    
    signal = state.get("proposed_signal")
    if not signal or signal.get("direction") == "neutral":
        state["validation_result"] = {"is_valid": False, "reason": "No trade or Neutral"}
        state["is_terminal"] = True
        return state
        
    try:
        # Instantiate the Rust struct
        engine = HftRulesEngine(
            min_confidence=0.6,
            min_rr=1.5,
            max_fear=75.0,
            kelly_cap_pct=0.20
        )
        
        # Fire native code validation
        is_val, kelly_val, reason = engine.validate_signal(
            signal.get("confidence", 0.0),
            signal.get("rr", 0.0),
            signal.get("fear_index", 50.0) # default fear to 50
        )
        
        state["validation_result"] = {
            "is_valid": is_val,
            "kelly_fraction": kelly_val,
            "reason": reason
        }
        
    except Exception as e:
        logger.error("Rust RiskGuard Engine crashed", err=str(e))
        state["errors"].append(f"Rust Validation Error: {e}")
        state["is_terminal"] = True
        
    return state

def portfolio_mind_node(state: GoldmineState) -> GoldmineState:
    """
    Finalizes the order text based on Kelly allocation and RiskGuard approval.
    """
    logger.info("Running PortfolioMind Node", symbol=state["symbol"])
    
    validation = state.get("validation_result")
    if validation and validation.get("is_valid"):
        pct = round(validation["kelly_fraction"] * 100, 2)
        state["execution_plan"] = f"EXECUTE: {state['proposed_signal'].get('direction').upper()} on {state['symbol']} using {pct}% of portfolio. Reason: Validation Passed."
    else:
        reason = validation.get("reason", "Unknown") if validation else "No Validation Data"
        state["execution_plan"] = f"REJECTED: Do not trade {state['symbol']}. Reason: {reason}"
        
    state["is_terminal"] = True
    return state
