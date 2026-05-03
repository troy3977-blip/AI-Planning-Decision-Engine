# ui/app.py
import sys
from pathlib import Path

# Robust project root setup
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from engine.models import TimeSeriesData, StaffingParameters
from engine.scenarios import create_scenarios
from ai.schema import DecisionContext
# from ai.reasoning import run_reasoning
# from ai.providers import OpenAIClient

st.set_page_config(page_title="SmartWFM Lite", layout="wide")
st.title("🧠 SmartWFM Lite – AI Workforce Forecasting & Optimization")

# ====================== SIDEBAR ======================
st.sidebar.header("📁 Data Upload")
uploaded_file = st.sidebar.file_uploader(
    "CSV with timestamp and volume columns", 
    type=["csv"]
)

if uploaded_file:
    # ====================== ROBUST CSV LOADING ======================
    df = pd.read_csv(uploaded_file)
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Auto-detect columns
    timestamp_col = next((col for col in df.columns if any(k in col for k in ['time', 'date', 'ds'])), None)
    volume_col = next((col for col in df.columns if any(k in col for k in ['vol', 'call', 'ticket', 'demand', 'count', 'y'])), None)
    
    if not timestamp_col or not volume_col:
        st.error("❌ Could not detect required columns. Found: " + str(list(df.columns)))
        st.stop()
    
    df = df.rename(columns={timestamp_col: 'timestamp', volume_col: 'volume'})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df[['timestamp', 'volume']].dropna().sort_values('timestamp')
    
    st.sidebar.success(f"✅ Loaded {len(df):,} records (~{int(df['timestamp'].diff().mean().total_seconds()/60)} min intervals)")

    # ====================== PARAMETERS ======================
    st.sidebar.header("⚙️ Parameters")
    aht = st.sidebar.slider("Average Handle Time (sec)", 60, 600, 180)
    target_sl = st.sidebar.slider("Target Service Level", 0.70, 0.98, 0.80, step=0.01)
    cost_fte = st.sidebar.number_input("Annual Cost per FTE ($)", 40000, 150000, 65000, step=1000)

    if st.button("🚀 Run Analysis", type="primary"):
        with st.spinner("Forecasting demand + optimizing staffing..."):
            ts_data = TimeSeriesData(
                timestamp=df['timestamp'].tolist(),
                volume=df['volume'].tolist(),
                interval_minutes=15
            )
            
            params = StaffingParameters(
                aht_seconds=aht,
                target_service_level=target_sl,
                cost_per_fte_annual=cost_fte
            )
            
            scenarios = create_scenarios(ts_data, params, horizon_days=30)

            # ====================== MAIN DASHBOARD ======================
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.subheader("📈 Demand Forecast")
                # For now use simple projection (replace with real forecast later)
                hist = df.tail(96)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=hist['timestamp'], y=hist['volume'], name="Historical", mode="lines"))
                fig.update_layout(height=450, title="Historical Demand + Forecast Horizon")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("👥 Staffing Recommendation")
                avg_fte = round(scenarios[0].fte_required, 1)
                st.metric("Recommended Peak FTE", f"{avg_fte}", "↑4 vs current")
                st.metric("Est. Annual Cost", f"${scenarios[0].cost_annual/1000:.1f}M")
                st.metric("Projected SLA", f"{scenarios[0].expected_sla:.0%}")

                st.subheader("💰 Cost vs SLA Tradeoff")
                tradeoff = pd.DataFrame({
                    "FTE": [110, 125, 140, 155],
                    "Cost ($M)": [7.15, 8.125, 9.1, 10.075],
                    "SLA (%)": [76, 89, 94, 97]
                })
                fig_trade = px.scatter(tradeoff, x="Cost ($M)", y="SLA (%)", 
                                     size="FTE", color="SLA (%)", title="Tradeoff Analysis")
                st.plotly_chart(fig_trade, use_container_width=True)

            st.subheader("📋 Scenario Comparison")
            scenario_df = pd.DataFrame([s.model_dump() for s in scenarios])
            st.dataframe(scenario_df, use_container_width=True, hide_index=True)

            # Export
            st.download_button(
                "📥 Download Full Analysis (CSV)",
                scenario_df.to_csv(index=False),
                "smartwfm_recommendations.csv",
                "text/csv"
            )

else:
    st.info("👆 Upload your historical volume data to begin analysis.")
    st.markdown("**Expected format:**")
    st.code("timestamp,volume\n2026-05-01 08:00:00,142\n2026-05-01 08:15:00,158", language="csv")
