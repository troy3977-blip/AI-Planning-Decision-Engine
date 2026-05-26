# ui/app.py
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ai.schema import DecisionContext  # noqa: E402
from engine.forecasting import generate_forecast  # noqa: E402
from engine.models import StaffingParameters, TimeSeriesData  # noqa: E402
from engine.scenarios import create_scenarios  # noqa: E402

load_dotenv()

st.set_page_config(page_title="SmartWFM Lite", layout="wide")
st.title("🧠 SmartWFM Lite – AI Workforce Forecasting & Optimization")

st.sidebar.header("📁 Data Upload")
uploaded_file = st.sidebar.file_uploader("CSV: timestamp, volume", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
    
    timestamp_col = next((col for col in df.columns if any(k in col for k in ['time','date','ds','timestamp'])), None)
    volume_col = next((col for col in df.columns if any(k in col for k in ['vol','volume','call','ticket','demand','count','y'])), None)
    
    if not timestamp_col or not volume_col:
        st.error("Could not detect timestamp and volume columns.")
        st.stop()
    
    df = df.rename(columns={timestamp_col: 'timestamp', volume_col: 'volume'})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df[['timestamp', 'volume']].dropna().sort_values('timestamp')
    
    st.sidebar.success(f"✅ Loaded {len(df):,} records")

    st.sidebar.header("⚙️ Parameters")
    aht = st.sidebar.slider("AHT (seconds)", 60, 600, 180)
    target_sl = st.sidebar.slider("Target Service Level", 0.70, 0.98, 0.80, step=0.01)
    cost_fte = st.sidebar.number_input("Annual Cost per FTE ($)", 40000, 150000, 65000, step=1000)

    if st.button("🚀 Run Full Analysis", type="primary"):
        with st.spinner("Running forecast + optimization..."):
            ts_data = TimeSeriesData(timestamp=df['timestamp'].tolist(), volume=df['volume'].tolist(), interval_minutes=15)
            params = StaffingParameters(aht_seconds=aht, target_service_level=target_sl, cost_per_fte_annual=cost_fte)
            
            forecast_result = generate_forecast(ts_data, horizon_days=30)
            scenarios = create_scenarios(ts_data, params, horizon_days=30)

            # AI with graceful fallback
            ai_summary = "AI recommendations require OPENAI_API_KEY in .env"
            try:
                if os.getenv("OPENAI_API_KEY"):
                    from ai.reasoning import run_reasoning
                    from ai.providers import OpenAIClient
                    ctx = DecisionContext(objective="balanced", decision_mode="recommend")
                    ai_result = run_reasoning(OpenAIClient(), ctx, scenarios)
                    ai_summary = ai_result.response.exec_summary if hasattr(ai_result, 'response') else ai_summary
            except Exception as exc:
                ai_summary = f"AI recommendations unavailable: {exc}"

            col1, col2 = st.columns([3, 2])
            with col1:
                st.subheader("📈 Demand Forecast")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['volume'], name="Historical"))
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("🤖 AI Recommendation")
                st.info(ai_summary)
                for sc in scenarios[:3]:
                    st.metric(sc.name, f"{sc.fte_required} FTE", f"${sc.cost_annual:,.0f}")

            st.subheader("📊 Scenarios")
            st.dataframe(pd.DataFrame([s.model_dump() for s in scenarios]), use_container_width=True)

            st.download_button("📥 Export Results", pd.DataFrame([s.model_dump() for s in scenarios]).to_csv(index=False), "smartwfm_results.csv")

else:
    st.info("Upload data or use sample below.")
    
    if st.button("📥 Download Sample CSV (9 Hours Realistic Data)"):
        start = datetime(2026, 5, 1, 8, 0)
        data = []
        for i in range(9*4 + 12):
            ts = start + timedelta(minutes=15*i)
            hour = ts.hour
            factor = 1.35 if 11 <= hour <= 14 else 1.0 if 8 <= hour <= 17 else 0.65
            volume = max(35, int(145 * factor + np.random.normal(0, 18)))
            data.append({"timestamp": ts, "volume": volume})
        sample_df = pd.DataFrame(data)
        st.download_button("⬇️ Download sample_call_volume.csv", sample_df.to_csv(index=False), "sample_call_volume.csv", "text/csv")
