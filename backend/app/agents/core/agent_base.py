"""
AgentBase – Abstract base class for all Goldmine agents.
Each specialized agent extends this with its own system prompt and tool set.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
import structlog

logger = structlog.get_logger()


class AgentBase(ABC):
    """
    Base class for Goldmine agents following the OpenClaw pattern:
    Plan → Reason → Act → Reflect
    """

    def __init__(self, llm_backbone, tool_registry, memory, task_id: str):
        self.llm = llm_backbone
        self.registry = tool_registry
        self.memory = memory
        self.task_id = task_id
        self._log_emitter: Optional[Callable] = None
        self.trace: list[dict] = []

    def set_log_emitter(self, emitter: Callable) -> None:
        """Register a callback to emit real-time log events."""
        self._log_emitter = emitter

    async def _emit(self, phase: str, message: str, data: Optional[dict] = None) -> None:
        log_entry = {
            "task_id": self.task_id,
            "agent": self.name,
            "phase": phase,
            "message": message,
            "data": data or {},
        }
        self.trace.append(log_entry)
        logger.info("Agent log", **log_entry)
        if self._log_emitter:
            await self._log_emitter(log_entry)

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name shown in UI (e.g. 'TrendMiner')."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining the agent's role."""
        ...

    @property
    @abstractmethod
    def tools(self) -> list[str]:
        """List of tool names this agent is allowed to use."""
        ...

    @abstractmethod
    async def run(self, context: dict) -> dict:
        """
        Execute the agent against the given context.
        Returns a result dict to be merged into the pipeline context.
        """
        ...

    async def _plan(self, task_description: str) -> str:
        """Phase 1: Decompose the task into a step-by-step plan."""
        await self._emit("plan", f"Planning how to {task_description[:80]}...")
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Create a step-by-step plan for: {task_description}"},
        ]
        resp = await self.llm.chat(messages, temperature=0.1, max_tokens=512)
        plan = resp["content"]
        await self._emit("plan", f"Plan ready ({len(plan.split())} words)")
        return plan

    async def _reason_and_act(
        self, messages: list[dict], max_iterations: int = 5
    ) -> tuple[str, list[dict]]:
        """Phase 2+3: Iterative reason → call tool → observe loop."""
        tool_manifest = self.registry.get_tool_manifest(self.tools)
        all_tool_results = []

        for i in range(max_iterations):
            resp = await self.llm.chat(messages, tools=tool_manifest, temperature=0.2)

            if not resp["tool_calls"]:
                # No more tool calls – final answer
                return resp["content"], all_tool_results

            for tc in resp["tool_calls"]:
                tool_name = tc["name"]
                tool_args = tc["args"]
                await self._emit("act", f"→ Calling {tool_name}", {"args": tool_args})

                try:
                    result = await self.registry.execute(tool_name, tool_args)
                    result_str = str(result)[:2000]
                    await self._emit("act", f"← {tool_name} returned ({len(result_str)} chars)")
                    all_tool_results.append({"tool": tool_name, "result": result})
                except Exception as e:
                    result_str = f"Error: {e}"
                    await self._emit("act", f"⚠ {tool_name} error: {e}")

                # Append assistant + tool result to messages
                messages.append({"role": "assistant", "content": resp["content"],
                                  "tool_calls": [{"id": tc["id"], "type": "function",
                                                  "function": {"name": tool_name,
                                                               "arguments": str(tool_args)}}]})
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result_str})

        return "", all_tool_results

    async def _reflect(self, result: Any, context: dict) -> str:
        """Phase 4: Evaluate result quality and update short-term memory."""
        await self._emit("reflect", "Reflecting on results...")
        summary_prompt = f"Summarize the key findings from: {str(result)[:1000]}"
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": summary_prompt},
        ]
        resp = await self.llm.chat(messages, temperature=0.2, max_tokens=256)
        summary = resp["content"]
        self.memory.add(f"[{self.name}] {summary}", metadata={"task_id": self.task_id})
        await self._emit("reflect", "✓ Memory updated with findings")
        return summary
