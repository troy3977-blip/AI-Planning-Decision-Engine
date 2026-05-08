# SmartWFM Lite

**AI-Powered Workforce Forecasting & Optimization for SMBs**

A fast, practical SaaS tool that helps operations managers at 50–500 employee companies forecast demand and optimize staffing with clear $ impact.

## Current Capabilities

- Smart CSV upload with flexible column detection
- Prophet forecasting with confidence bands
- Erlang-C based staffing recommendations
- Scenario analysis (Base / Optimistic / Pessimistic)
- Interactive Plotly visualizations
- AI-powered executive summaries (optional)
- Sample data generator (realistic 9+ hour dataset)

## Tech Stack

- **Backend**: Python, Prophet, SciPy, Pandas
- **Frontend**: Streamlit + Plotly
- **Deployment**: Azure App Service
- **Automation**: GitHub Actions CI/CD + Dependabot

## Quick Local Run

```bash
source .venv/bin/activate
export PYTHONPATH=$(pwd)
streamlit run ui/app.py