from ai.schema import DecisionContext, Scenario
from ai.reasoning import run_reasoning
from ai.providers import OpenAIClient

scenarios = [
    Scenario(
        scenario_id="S1",
        name="Balanced",
        fte_required=120,
        cost_annual=8_400_000,
        expected_sla=0.82,
        breach_risk=0.09,
        occupancy_peak=0.91,
    ),
    Scenario(
        scenario_id="S2",
        name="Cost-Min",
        fte_required=110,
        cost_annual=7_700_000,
        expected_sla=0.78,
        breach_risk=0.18,
        occupancy_peak=0.95,
    ),
]

ctx = DecisionContext(
    objective="balanced",
    decision_mode="recommend",
    audience="exec",
    min_sla_target=0.80,
    max_breach_risk=0.10,
)

result = run_reasoning(OpenAIClient(), ctx, scenarios)

print("\nEXEC SUMMARY")
print(result.response.exec_summary)

if result.response.recommendation:
    print("\nRECOMMENDED SCENARIO")
    print(result.response.recommendation)