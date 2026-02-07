# ai/schema.py
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


Audience = Literal["exec", "ops_manager", "analyst"]
DecisionMode = Literal["recommend", "compare", "qa"]
Objective = Literal["min_cost", "max_sla", "balanced", "risk_averse"]


class DecisionContext(BaseModel):
    """Inputs that shape how the AI should reason about the scenario set."""
    model_config = ConfigDict(extra="forbid")

    objective: Objective = "balanced"
    decision_mode: DecisionMode = "recommend"
    audience: Audience = "ops_manager"

    # Optional constraints (interpreted by your deterministic engine first; AI uses them for narrative)
    min_sla_target: Optional[float] = None  # e.g. 0.80
    max_budget_annual: Optional[float] = None
    max_breach_risk: Optional[float] = None  # e.g. 0.10
    notes: Optional[str] = None


class Scenario(BaseModel):
    """Authoritative scenario metrics computed by your engine."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)

    fte_required: float
    cost_annual: float
    expected_sla: float  # 0..1
    breach_risk: float   # 0..1
    occupancy_peak: Optional[float] = None  # 0..1
    notes: Optional[str] = None

    @field_validator("expected_sla", "breach_risk")
    @classmethod
    def _bounded_01(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Value must be in [0, 1].")
        return v

    @field_validator("occupancy_peak")
    @classmethod
    def _occ_bounded(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if not (0.0 <= v <= 1.0):
            raise ValueError("occupancy_peak must be in [0, 1].")
        return v


class Citation(BaseModel):
    """Grounding evidence: scenario_id + which fields were used."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    fields: List[str]


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)

    why: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)


class Tradeoff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimension: str
    winner: str  # scenario_id
    note: str


class Comparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_2: List[str] = Field(default_factory=list)  # scenario_ids
    tradeoffs: List[Tradeoff] = Field(default_factory=list)


class AIResponse(BaseModel):
    """Structured output the UI and audit log can rely on."""
    model_config = ConfigDict(extra="forbid")

    recommendation: Optional[Recommendation] = None
    comparison: Optional[Comparison] = None

    exec_summary: str
    citations: List[Citation] = Field(default_factory=list)

    # Optional Q&A response fields
    answer: Optional[str] = None
    missing_data: Optional[List[str]] = None
    suggested_reruns: Optional[List[Dict[str, Any]]] = None


def scenario_index(scenarios: List[Scenario]) -> Dict[str, Scenario]:
    return {s.scenario_id: s for s in scenarios}