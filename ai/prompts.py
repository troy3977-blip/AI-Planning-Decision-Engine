# ai/prompts.py
from __future__ import annotations

import json
from typing import Any, Dict, List

from .schema import DecisionContext, Scenario


SYSTEM_PROMPT = """You are a workforce-planning decision support assistant.

NON-NEGOTIABLE RULES:
- Use ONLY the scenario data and decision context provided in the user message.
- Do NOT compute new staffing, SLA, costs, savings, deltas, or probabilities.
- Do NOT invent new scenarios, constraints, or metrics.
- If the user asks for something that requires recomputation by the engine, say so and list what inputs must be rerun.
- Output MUST be valid JSON and MUST match the required schema.
- Always ground claims: include citations of scenario_id + the exact fields you used.

OUTPUT FORMAT:
Return ONLY JSON. No markdown. No extra text.
"""


def _scenarios_to_json(scenarios: List[Scenario]) -> List[Dict[str, Any]]:
    return [s.model_dump() for s in scenarios]


def build_user_payload(
    ctx: DecisionContext,
    scenarios: List[Scenario],
    user_question: str | None = None,
) -> str:
    """Build the single authoritative payload the model must use."""
    payload: Dict[str, Any] = {
        "decision_context": ctx.model_dump(),
        "scenarios": _scenarios_to_json(scenarios),
        "user_question": user_question or "",
        "schema_contract": {
            "required_top_level_keys": ["exec_summary", "citations"],
            "recommend_mode": "Include 'recommendation' with scenario_id, confidence, why/risks/assumptions/next_actions.",
            "compare_mode": "Include 'comparison' with top_2 and tradeoffs.",
            "qa_mode": "Include 'answer'. If unknown, include 'missing_data' and 'suggested_reruns'.",
            "citations_rule": "Every major claim must cite scenario_id and fields used (e.g., expected_sla, cost_annual, breach_risk, occupancy_peak, fte_required).",
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def build_mode_instruction(ctx: DecisionContext) -> str:
    if ctx.decision_mode == "recommend":
        return (
            "TASK: Recommend the best scenario given the context. "
            "First filter infeasible scenarios if constraints are present, then choose based on objective. "
            "Provide concise exec_summary tailored to audience."
        )
    if ctx.decision_mode == "compare":
        return (
            "TASK: Compare scenarios and select the top 2 contenders. "
            "Provide tradeoffs (cost vs risk vs SLA) and an exec_summary tailored to audience."
        )
    if ctx.decision_mode == "qa":
        return (
            "TASK: Answer the user's question using ONLY the provided scenario table. "
            "If the question requires recomputation (e.g., changing AHT/forecast/shrinkage), say so and return missing_data + suggested_reruns."
        )
    return "TASK: Provide decision support using only the provided payload."