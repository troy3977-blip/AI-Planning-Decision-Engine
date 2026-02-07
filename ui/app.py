import streamlit as st

from ai.schema import DecisionContext, Scenario
from ai.reasoning import run_reasoning
from ai.providers import OpenAIClient
from ui.components.ai_panels import render_ai_decision_panel

st.title("Workforce Planning Decision Engine")

# Example scenarios (replace with your engine outputs)
scenarios = [
    Scenario(scenario_id="S1", name="Balanced", fte_required=120, cost_annual=8_400_000,
             expected_sla=0.82, breach_risk=0.09, occupancy_peak=0.91),
    Scenario(scenario_id="S2", name="Cost-Min", fte_required=110, cost_annual=7_700_000,
             expected_sla=0.78, breach_risk=0.18, occupancy_peak=0.95),
    Scenario(scenario_id="S3", name="Risk-Averse", fte_required=128, cost_annual=8_900_000,
             expected_sla=0.86, breach_risk=0.05, occupancy_peak=0.88),
]

ctx = DecisionContext(objective="balanced", decision_mode="recommend", audience="exec", min_sla_target=0.80, max_breach_risk=0.10)

if st.button("Run AI reasoning"):
    llm = OpenAIClient()
    result = run_reasoning(llm, ctx, scenarios)
    st.session_state["ai_result"] = result

if "ai_result" in st.session_state:
    selected = render_ai_decision_panel(
        result=st.session_state["ai_result"],
        scenarios=scenarios,
        key_prefix="main",
    )
    st.success(f"Selected scenario: {selected}")
else:
    st.info("Click 'Run AI reasoning' to generate recommendations and citations.")