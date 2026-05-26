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

## Deployment & Custom Domain

### Production Deployment
- Deployed to Azure App Service: `smartwfm-lite.azurewebsites.net`
- Auto-deployment via GitHub Actions on main branch push
- See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment details

### Custom Domain Integration
To connect your own domain name (e.g., `wfm.example.com`):

1. **Quick Setup**: Run the domain setup script
   ```bash
   chmod +x scripts/setup-domain.sh
   ./scripts/setup-domain.sh your-domain.com your-resource-group
   ```

2. **Detailed Guide**: See [DOMAIN_INTEGRATION.md](docs/DOMAIN_INTEGRATION.md)

3. **Setup Checklist**: Follow [DOMAIN_SETUP_CHECKLIST.md](docs/DOMAIN_SETUP_CHECKLIST.md) step-by-step

4. **DNS Configuration**: Track your records in [DNS_CONFIGURATION_RECORD.md](docs/DNS_CONFIGURATION_RECORD.md)

5. **GitHub Actions**: Automated domain setup workflow available (`.github/workflows/setup-domain.yml`)

## Quick Local Run

```bash
source .venv/bin/activate
export PYTHONPATH=$(pwd)
streamlit run ui/app.py