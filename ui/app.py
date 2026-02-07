from ai.schema import DecisionContext, Scenario
from ai.reasoning import run_reasoning
from ai.providers.openai_client import OpenAIClient

llm = OpenAIClient()  # reads OPENAI_API_KEY and OPENAI_MODEL

ctx = DecisionContext(
    objective="balanced",
    decision_mode="recommend",
    audience="exec",
    min_sla_target=0.80,
    max_breach_risk=0.10,
)

scenarios = [
    Scenario(
        scenario_id="S1",
        name="Balanced",
        fte_required=120.0,
        cost_annual=8_400_000.0,
        expected_sla=0.82,
        breach_risk=0.09,
        occupancy_peak=0.91,
    ),
    Scenario(
        scenario_id="S2",
        name="Cost-Min",
        fte_required=110.0,
        cost_annual=7_700_000.0,
        expected_sla=0.78,
        breach_risk=0.18,
        occupancy_peak=0.95,
    ),
]

result = run_reasoning(llm, ctx, scenarios)
print(result.response.exec_summary)
print(result.issues)