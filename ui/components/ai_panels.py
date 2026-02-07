# ui/components/ai_panels.py
from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Optional

import streamlit as st

from ai.schema import AIResponse, Scenario
from ai.reasoning import AIResult, ValidationIssue


def _issue_lines(issues: List[ValidationIssue]) -> List[str]:
    lines = []
    for iss in issues:
        # iss might be dataclass ValidationIssue; handle both dict-like and attribute-like
        t = getattr(iss, "type", None) or (iss.get("type") if isinstance(iss, dict) else "issue")
        m = getattr(iss, "message", None) or (iss.get("message") if isinstance(iss, dict) else str(iss))
        lines.append(f"**{t}**: {m}")
    return lines


def render_ai_decision_panel(
    *,
    result: AIResult,
    scenarios: List[Scenario],
    title: str = "AI Decision Support",
    default_selected_scenario_id: Optional[str] = None,
    key_prefix: str = "ai_panel",
) -> Optional[str]:
    """
    Renders:
      - warnings if result.issues is non-empty
      - exec summary
      - recommendation block (if present)
      - citations as clickable chips that select a scenario_id
    Returns:
      - selected scenario_id if user clicked a chip or used selector
      - otherwise the current selection
    """
    scenario_map: Dict[str, Scenario] = {s.scenario_id: s for s in scenarios}
    resp: AIResponse = result.response

    st.subheader(title)

    # --- Warnings / validation issues ---
    if result.issues:
        st.warning("AI output validation warnings detected. Review before acting.", icon="⚠️")
        with st.expander("Show validation issues", expanded=False):
            for line in _issue_lines(result.issues):
                st.markdown(f"- {line}")

    # --- Exec summary ---
    st.markdown("#### Executive Summary")
    st.write(resp.exec_summary)

    # --- Scenario selection state ---
    state_key = f"{key_prefix}_selected_scenario_id"
    if state_key not in st.session_state:
        # Prefer recommended scenario, else provided default, else first scenario
        init = None
        if resp.recommendation and resp.recommendation.scenario_id in scenario_map:
            init = resp.recommendation.scenario_id
        elif default_selected_scenario_id and default_selected_scenario_id in scenario_map:
            init = default_selected_scenario_id
        elif scenarios:
            init = scenarios[0].scenario_id
        st.session_state[state_key] = init

    # --- Recommendation (if present) ---
    if resp.recommendation:
        rec = resp.recommendation
        st.markdown("#### Recommendation")

        cols = st.columns([2, 1])
        with cols[0]:
            st.markdown(f"**Recommended:** `{rec.scenario_id}` — {scenario_map.get(rec.scenario_id, Scenario(  # type: ignore
                scenario_id=rec.scenario_id, name="(unknown)", fte_required=0, cost_annual=0, expected_sla=0, breach_risk=0
            )).name}")
        with cols[1]:
            st.metric("Confidence", f"{rec.confidence:.0%}")

        if rec.why:
            st.markdown("**Why this scenario**")
            for w in rec.why:
                st.markdown(f"- {w}")

        if rec.risks:
            st.markdown("**Risks / watchouts**")
            for r in rec.risks:
                st.markdown(f"- {r}")

        if rec.assumptions:
            with st.expander("Assumptions", expanded=False):
                for a in rec.assumptions:
                    st.markdown(f"- {a}")

        if rec.next_actions:
            with st.expander("Next actions", expanded=False):
                for n in rec.next_actions:
                    st.markdown(f"- {n}")

    # --- Citations as clickable chips ---
    st.markdown("#### Evidence (Citations)")
    if not resp.citations:
        st.info("No citations provided.")
    else:
        # Build unique list of cited scenario_ids preserving order
        cited_ids: List[str] = []
        cited_fields: Dict[str, List[str]] = {}
        for c in resp.citations:
            sid = c.scenario_id
            if sid not in cited_ids:
                cited_ids.append(sid)
            cited_fields.setdefault(sid, [])
            for f in c.fields:
                if f not in cited_fields[sid]:
                    cited_fields[sid].append(f)

        # Render chips in rows
        chip_cols = st.columns(min(4, max(1, len(cited_ids))))
        for i, sid in enumerate(cited_ids):
            col = chip_cols[i % len(chip_cols)]
            with col:
                label = sid
                if st.button(label, key=f"{key_prefix}_chip_{sid}"):
                    st.session_state[state_key] = sid

        # Details for selected citation scenario
        selected = st.session_state[state_key]
        if selected in scenario_map:
            s = scenario_map[selected]
            st.markdown(f"**Selected scenario:** `{s.scenario_id}` — {s.name}")
            fields = cited_fields.get(selected, [])
            if fields:
                st.caption("Cited fields: " + ", ".join(fields))

            # Small, readable scenario snapshot
            with st.expander("Scenario details", expanded=False):
                st.markdown(
                    f"""
- **FTE Required:** {s.fte_required:,.2f}
- **Annual Cost:** ${s.cost_annual:,.0f}
- **Expected SLA:** {s.expected_sla:.0%}
- **Breach Risk:** {s.breach_risk:.0%}
- **Peak Occupancy:** {("" if s.occupancy_peak is None else f"{s.occupancy_peak:.0%}") }
"""
                )
                if s.notes:
                    st.markdown(f"**Notes:** {s.notes}")
        else:
            st.caption("Click a citation chip to select a scenario.")

    # --- Optional: Manual selector (nice fallback) ---
    st.markdown("#### Select Scenario")
    option_ids = [s.scenario_id for s in scenarios]
    chosen = st.selectbox(
        "Scenario",
        options=option_ids,
        index=option_ids.index(st.session_state[state_key]) if st.session_state[state_key] in option_ids else 0,
        key=f"{key_prefix}_selectbox",
    )
    st.session_state[state_key] = chosen

    return st.session_state[state_key]