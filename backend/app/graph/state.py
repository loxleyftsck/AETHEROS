"""
LangGraph State Definition for AgentOS Goldmine v3.
"""
from typing import TypedDict, List, Dict, Any, Optional

class GoldmineState(TypedDict):
    """
    Represents the state passed between LangGraph nodes during execution.
    """
    task_id: str
    symbol: str
    
    # 1. Output from Phase 3 CrewAI Research Mesh
    research_context: Optional[str]
    
    # 2. Output from SignalForge Node
    proposed_signal: Optional[Dict[str, Any]] # e.g., {"direction": "long", "confidence": 0.85, "rr": 2.0}
    
    # 3. Output from RiskGuard Node (Rust Engine results)
    validation_result: Optional[Dict[str, Any]] # e.g., {"is_valid": true, "kelly_fraction": 0.20, "reason": "..."}
    
    # 4. Final Execution Plan
    execution_plan: Optional[str]
    
    # Status flags
    errors: List[str]
    is_terminal: bool
