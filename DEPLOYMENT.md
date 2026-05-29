# SmartWFM Lite Deployment Integration Guide

This repository is prepared for Azure App Service, but the Azure resource itself must be configured outside this workspace. Use this guide to update the exact settings required for the Streamlit app to run correctly.

## Recommended Path: Azure App Service Source Deployment

Use this path when GitHub Actions deploys the repository directly with `azure/webapps-deploy`.

### 1. GitHub Repository Settings

In GitHub, go to:

`Repository -> Settings -> Secrets and variables -> Actions -> New repository secret`

Add:

| Secret | Value |
| --- | --- |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | The publish profile downloaded from the Azure App Service |

If you use the custom-domain workflow, also add:

| Secret | Value |
| --- | --- |
| `AZURE_CREDENTIALS` | Azure service principal JSON for `azure/login` |

### 2. GitHub Actions Deploy Workflow

Confirm [.github/workflows/deploy.yml](.github/workflows/deploy.yml) contains this startup command:

```yaml
startup-command: python -m streamlit run ui/app.py --server.address=0.0.0.0 --server.port=8000
```

Azure source-based Python App Service deployments commonly expect the process to listen on port `8000`. This startup command overrides Azure's default Python app detection and starts Streamlit directly.

### 3. Azure App Service Configuration

In Azure Portal, open:

`App Service -> Configuration -> General settings`

Update:

| Setting | Value |
| --- | --- |
| Stack | Python |
| Python version | `3.12` |
| Startup Command | `python -m streamlit run ui/app.py --server.address=0.0.0.0 --server.port=8000` |

Then open:

`App Service -> Configuration -> Application settings`

Add or confirm:

| Name | Value |
| --- | --- |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |
| `PYTHONPATH` | `/home/site/wwwroot` |
| `STREAMLIT_SERVER_HEADLESS` | `true` |
| `STREAMLIT_CLIENT_SHOW_ERROR_DETAILS` | `none` |
| `OPENAI_API_KEY` | Your key, only if AI summaries should be enabled |
| `OPENAI_MODEL` | Optional model override |

Restart the App Service after saving configuration changes.

### 4. Streamlit Repository Configuration

Confirm [.streamlit/config.toml](.streamlit/config.toml) is committed and contains valid TOML:

```toml
[server]
headless = true
address = "0.0.0.0"
port = 8501
```

The GitHub/Azure startup command sets port `8000` for App Service. The local config can stay on `8501` for local runs and Docker.

### 5. Deployment Package Hygiene

Before committing deployment changes, avoid shipping local artifacts:

```bash
git status --short
```

These should not be tracked in Git:

- `.venv/`
- `.venv-1/`
- `venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.env`
- `run.exe`

If they are already tracked and you are ready to remove them from Git tracking, run:

```bash
git rm -r --cached .venv-1 run.exe
git commit -m "chore: remove local environment artifacts from deployment package"
```

This does not delete the local files; it only removes them from the Git index.

## Alternative Path: Docker Deployment

Use this path only if the Azure Web App is configured for a custom container.

### 1. Azure App Service Container Settings

In Azure Portal, open:

`App Service -> Deployment Center` or `App Service -> Configuration`

Configure the container image built from [Dockerfile](Dockerfile).

Add this application setting:

| Name | Value |
| --- | --- |
| `WEBSITES_PORT` | `8501` |

The Dockerfile starts Streamlit on port `8501`, so Azure must route traffic to that port.

### 2. Docker Build Context

Confirm [.dockerignore](.dockerignore) is committed. It prevents local secrets, virtual environments, caches, and generated files from entering the image.

## Custom Domain Integration

Custom domains are separate from app startup. Configure app startup first, then use the domain docs:

- [docs/DOMAIN_SETUP_CHECKLIST.md](docs/DOMAIN_SETUP_CHECKLIST.md)
- [docs/DOMAIN_INTEGRATION.md](docs/DOMAIN_INTEGRATION.md)
- [docs/DNS_CONFIGURATION_RECORD.md](docs/DNS_CONFIGURATION_RECORD.md)

Expected flow:

1. Confirm `https://smartwfmai.azurewebsites.net` loads.
2. Add the custom hostname in Azure App Service.
3. Add DNS records at the domain registrar.
4. Create and bind an Azure managed certificate.
5. Enable HTTPS-only.

## Verification Checklist

Run locally before pushing:

```bash
pytest tests/ -q
python -m streamlit config show
python -c "import config.settings; import ai.providers.openai_client; print('imports ok')"
```

After deployment, check:

```bash
curl -I https://smartwfmai.azurewebsites.net
```

Expected result:

- HTTP status is `200`, `302`, or another non-`5xx` response.
- Azure Log Stream does not show `ModuleNotFoundError`.
- Azure Log Stream does not show Streamlit config parse errors.
- Azure Log Stream shows Streamlit listening on `0.0.0.0:8000` for source deployments.

## Common Failure Points

| Symptom | Likely Cause | Update |
| --- | --- | --- |
| Azure default page or app fails to start | Missing startup command | Set the startup command in Azure and `.github/workflows/deploy.yml` |
| `ModuleNotFoundError: pydantic_settings` | Missing dependency | Confirm `pydantic-settings` exists in `requirements.txt` |
| Streamlit TOML parse error | Invalid `.streamlit/config.toml` | Quote `address = "0.0.0.0"` and remove unsupported keys |
| App works locally but not in Azure | Wrong port | Use port `8000` for source deploys, `8501` plus `WEBSITES_PORT=8501` for Docker |
| Deployment package is huge or slow | Local virtualenv tracked | Remove tracked env artifacts with `git rm --cached` |
| Custom domain opens but app fails | Startup/runtime issue, not DNS | Fix App Service startup first, then revisit domain binding |
