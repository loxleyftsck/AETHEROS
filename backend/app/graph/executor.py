"""
Compiles the LangGraph StateMachine for Phase 4.
"""
from langgraph.graph import StateGraph, END
import structlog

from .state import GoldmineState
from .nodes import signal_forge_node, risk_guard_node, portfolio_mind_node

logger = structlog.get_logger()

# 1. Initialize Graph
workflow = StateGraph(GoldmineState)

# 2. Add Nodes
workflow.add_node("SignalForge", signal_forge_node)
workflow.add_node("RiskGuard", risk_guard_node)
workflow.add_node("PortfolioMind", portfolio_mind_node)

# 3. Add Edges (Sequence)
workflow.add_edge("SignalForge", "RiskGuard")
workflow.add_edge("RiskGuard", "PortfolioMind")
workflow.add_edge("PortfolioMind", END)

# Set the Entry Point
workflow.set_entry_point("SignalForge")

# Compile the execution graph
app_executor = workflow.compile()

async def run_trading_graph(state_initial: dict) -> dict:
    """
    Executes the compiled LangGraph routing.
    """
    logger.info("LangGraph Execution Started", task_id=state_initial.get("task_id"))
    final_state = await app_executor.ainvoke(state_initial)
    logger.info("LangGraph Execution Finished", task_id=state_initial.get("task_id"))
    return final_state
