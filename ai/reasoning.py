from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol  # ← remove Tuple

from pydantic import ValidationError

from .schema import AIResponse, DecisionContext, Scenario, scenario_index
from .prompts import SYSTEM_PROMPT, build_mode_instruction, build_user_payload


# ----------------------------
# Provider interface (agnostic)
# ----------------------------

class LLMClient(Protocol):
    def complete_json(self, *, system: str, user: str) -> str:
        """Return a raw string (expected JSON). Provider must NOT add markdown wrappers."""
        ...

# ----------------------------
# Errors / results
# ----------------------------

class AIResponseError(Exception):
    pass


@dataclass
class ValidationIssue:
    type: str
    message: str


@dataclass
class AIResult:
    response: AIResponse
    raw_json: Dict[str, Any]
    issues: List[ValidationIssue]


# ----------------------------
# Validation (grounding)
# ----------------------------

ALLOWED_CITATION_FIELDS = {
    "scenario_id",
    "name",
    "fte_required",
    "cost_annual",
    "expected_sla",
    "breach_risk",
    "occupancy_peak",
    "notes",
}

def _parse_json_strict(text: str) -> Dict[str, Any]:
    # Common failure: model returns extra text. We enforce pure JSON.
    text = text.strip()
    if not text.startswith("{") or not text.endswith("}"):
        raise AIResponseError("Model did not return a pure JSON object.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise AIResponseError(f"Invalid JSON: {e}") from e


def _validate_citations(payload: Dict[str, Any], scenarios: List[Scenario]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    idx = scenario_index(scenarios)

    citations = payload.get("citations", [])
    if not isinstance(citations, list):
        return [ValidationIssue("citations", "citations must be a list.")]

    for i, c in enumerate(citations):
        if not isinstance(c, dict):
            issues.append(ValidationIssue("citations", f"citations[{i}] must be an object."))
            continue
        sid = c.get("scenario_id")
        fields = c.get("fields")
        if sid not in idx:
            issues.append(ValidationIssue("citations", f"citations[{i}].scenario_id '{sid}' not found in scenarios."))
        if not isinstance(fields, list) or not all(isinstance(f, str) for f in fields):
            issues.append(ValidationIssue("citations", f"citations[{i}].fields must be a list[str]."))
            continue
        bad = [f for f in fields if f not in ALLOWED_CITATION_FIELDS]
        if bad:
            issues.append(ValidationIssue("citations", f"citations[{i}] has invalid fields: {bad}"))

    # Minimum expectation: at least one citation for recommend/compare
    has_reco = payload.get("recommendation") is not None
    has_comp = payload.get("comparison") is not None
    if (has_reco or has_comp) and len(citations) == 0:
        issues.append(ValidationIssue("citations", "Expected at least one citation for recommendation/comparison outputs."))

    return issues


def _validate_references(payload: Dict[str, Any], scenarios: List[Scenario]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    idx = scenario_index(scenarios)

    reco = payload.get("recommendation")
    if isinstance(reco, dict):
        sid = reco.get("scenario_id")
        if sid and sid not in idx:
            issues.append(ValidationIssue("recommendation", f"recommendation.scenario_id '{sid}' not found."))

    comp = payload.get("comparison")
    if isinstance(comp, dict):
        top_2 = comp.get("top_2", [])
        if isinstance(top_2, list):
            for sid in top_2:
                if sid not in idx:
                    issues.append(ValidationIssue("comparison", f"comparison.top_2 contains unknown scenario_id '{sid}'"))
        tradeoffs = comp.get("tradeoffs", [])
        if isinstance(tradeoffs, list):
            for t in tradeoffs:
                if isinstance(t, dict):
                    win = t.get("winner")
                    if win and win not in idx:
                        issues.append(ValidationIssue("comparison", f"comparison.tradeoffs winner '{win}' not found."))

    return issues


def validate_ai_payload(payload: Dict[str, Any], scenarios: List[Scenario]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    issues.extend(_validate_citations(payload, scenarios))
    issues.extend(_validate_references(payload, scenarios))
    return issues


# ----------------------------
# Correction prompt builder
# ----------------------------

def build_correction_user_prompt(
    original_user_payload_json: str,
    model_output_text: str,
    issues: List[ValidationIssue],
) -> str:
    """Ask the model to repair its JSON without changing meaning beyond fixing issues."""
    issue_lines = "\n".join([f"- {iss.type}: {iss.message}" for iss in issues]) or "- (unknown)"
    return (
        "You returned JSON that failed validation.\n"
        "Fix the JSON to satisfy the schema and constraints.\n"
        "Do not add new numbers or claims. Do not change scenario data.\n"
        "Return ONLY corrected JSON.\n\n"
        "VALIDATION ISSUES:\n"
        f"{issue_lines}\n\n"
        "ORIGINAL AUTHORITATIVE USER PAYLOAD (do not contradict):\n"
        f"{original_user_payload_json}\n\n"
        "YOUR PRIOR OUTPUT:\n"
        f"{model_output_text.strip()}\n"
    )


# ----------------------------
# Main reasoning entrypoint
# ----------------------------

def run_reasoning(
    llm: LLMClient,
    ctx: DecisionContext,
    scenarios: List[Scenario],
    user_question: Optional[str] = None,
    max_attempts: int = 2,
) -> AIResult:
    """
    Executes AI reasoning with strict JSON + grounding validation.
    Retries once with a correction prompt if invalid.
    """
    if not scenarios:
        raise ValueError("scenarios must be non-empty")

    user_payload = build_user_payload(ctx, scenarios, user_question=user_question)
    user_prompt = f"{build_mode_instruction(ctx)}\n\nAUTHORITATIVE PAYLOAD:\n{user_payload}"

    last_text: Optional[str] = None
    last_payload: Optional[Dict[str, Any]] = None
    last_issues: List[ValidationIssue] = []

    for attempt in range(1, max_attempts + 1):
        text = llm.complete_json(system=SYSTEM_PROMPT, user=user_prompt)
        last_text = text

        payload = _parse_json_strict(text)
        last_payload = payload

        # Schema validation
        try:
            parsed = AIResponse.model_validate(payload)
        except ValidationError as e:
            last_issues = [ValidationIssue("schema", str(e))]
            if attempt < max_attempts:
                user_prompt = build_correction_user_prompt(user_payload, text, last_issues)
                continue
            raise AIResponseError(f"AIResponse schema validation failed: {e}") from e

        # Grounding validation
        issues = validate_ai_payload(payload, scenarios)
        last_issues = issues
        if issues and attempt < max_attempts:
            user_prompt = build_correction_user_prompt(user_payload, text, issues)
            continue
        if issues:
            # Return anyway with issues so UI can show warnings, but you can also choose to raise.
            return AIResult(response=parsed, raw_json=payload, issues=issues)

        return AIResult(response=parsed, raw_json=payload, issues=[])

    # Should never reach, but keep safe.
    raise AIResponseError(f"Failed to obtain valid AI output. Last: {last_text}, payload: {last_payload}, issues: {last_issues}")


# ----------------------------
# Optional: simple stub client
# ----------------------------

class DummyLLM:
    """
    For local testing without an LLM provider.
    Returns a minimal valid response that references the first scenario.
    """
    def __init__(self, scenario_id: str):
        self._scenario_id = scenario_id

    def complete_json(self, *, system: str, user: str) -> str:
        return json.dumps({
            "recommendation": {
                "scenario_id": self._scenario_id,
                "confidence": 0.5,
                "why": ["Stub output for wiring tests."],
                "risks": [],
                "assumptions": [],
                "next_actions": ["Connect a real provider implementation."]
            },
            "comparison": None,
            "exec_summary": f"Stub recommendation: {self._scenario_id}.",
            "citations": [{"scenario_id": self._scenario_id, "fields": ["expected_sla", "cost_annual", "breach_risk"]}]
        })