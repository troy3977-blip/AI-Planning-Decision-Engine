# Azure App Service + Custom Domain Integration Guide

## Overview
This guide walks you through integrating a custom domain name with your Azure App Service deployment of SmartWFM Lite.

## Prerequisites
- ✅ Azure App Service deployed (smartwfm-lite)
- ✅ GitHub Actions CI/CD pipeline configured
- Registered domain name (through any DNS provider)
- Azure CLI installed locally
- Contributor access to Azure subscription

## Step 1: Verify Your App Service

Before setting up the domain, verify your app is running:

```bash
# Check Azure login status
az account show

# If not logged in:
az login

# List your app services
az webapp list --output table
```

Your app should be listed as `smartwfm-lite` in resource group.

## Step 2: Prepare Your Custom Domain

### Option A: Domain Hosted on Azure DNS (Recommended)
If you want to manage DNS entirely in Azure:

1. Create an Azure DNS Zone
2. Update nameservers at your registrar to point to Azure DNS nameservers
3. Add DNS records in Azure

### Option B: Domain Hosted Elsewhere
If using external DNS provider (GoDaddy, Namecheap, etc.):

1. Keep DNS records with your provider
2. Add verification TXT records
3. Configure CNAME/A records to point to your App Service

## Step 3: Add Custom Domain to App Service (Azure Portal)

### Manual Approach:

1. Go to Azure Portal → App Services → smartwfm-lite
2. Select **Custom domains** from left menu
3. Click **+ Add custom domain**
4. Enter your domain name (e.g., `wfm.example.com`)
5. Choose validation method:
   - **CNAME validation** (easier) - Add CNAME record to DNS
   - **A record validation** - Use static IP

### CNAME Method (Recommended):
- Add CNAME record: `wfm` → `smartwfm-lite.azurewebsites.net`
- Wait for validation (usually 5-15 minutes)

### A Record Method:
- Azure will provide a static IP
- Add A record pointing to that IP

## Step 4: Enable HTTPS/SSL

1. In App Service **Custom domains** section
2. Click your domain
3. Click **Add binding**
4. Select App Service Managed Certificate (free)
5. Or use custom certificate if you have one

## Step 5: Configure App for Custom Domain

### Update Streamlit Settings

Edit `config/settings.py` or create `.streamlit/config.toml`:

```toml
[server]
headless = true
port = 8501
enableXsrfProtection = true
enableCORS = true

[client]
showErrorDetails = false
toolbarMode = "viewer"

# Only allow your domain
allowedOrigins = ["wfm.example.com", "*.example.com"]
```

### Update Environment Variables

Add to your App Service configuration:
```
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false
```

## Step 6: Test Domain Access

```bash
# Test DNS resolution
nslookup wfm.example.com

# Test HTTPS
curl -v https://wfm.example.com

# Test app availability
# Visit https://wfm.example.com in browser
```

## Troubleshooting

### Domain Not Resolving
```bash
# Check DNS propagation
nslookup wfm.example.com
dig wfm.example.com
```

### SSL Certificate Issues
- Check certificate status in App Service → Custom domains
- Manually renew if needed
- Use Azure Portal to issue/manage certificates

### CORS/HTTPS Redirect Issues
- Ensure HTTPS is enforced in App Service configuration
- Update Streamlit config to trust the domain
- Check browser console for blocked requests

### 403 Forbidden Errors
- Verify domain binding is correct
- Check IP restrictions aren't blocking the domain
- Review App Service access control

## Automated Setup via Azure CLI

Quick command-line setup:

```bash
# Set variables
RESOURCE_GROUP="your-resource-group"
APP_NAME="smartwfm-lite"
DOMAIN_NAME="wfm.example.com"

# Get the target hostname
TARGET_HOSTNAME=$(az webapp show -n $APP_NAME -g $RESOURCE_GROUP --query 'defaultHostName' -o tsv)

# Add custom domain binding
az webapp config hostname add \
  --webapp-name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --hostname $DOMAIN_NAME

# Create App Service managed certificate
az webapp config ssl bind \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --certificate-thumbprint <THUMBPRINT>
```

## Deployment Workflow Updates

Your current `deploy.yml` is configured for the app service deployment. After domain setup:

1. No workflow changes needed for domain binding
2. Domain is managed in Azure portal or via IaC
3. App automatically serves on both `smartwfm-lite.azurewebsites.net` and `wfm.example.com`

## DNS Configuration Examples

### For CNAME Method:
```
Type: CNAME
Name: wfm
Value: smartwfm-lite.azurewebsites.net
TTL: 3600
```

### For A Record Method:
```
Type: A
Name: wfm
Value: <static-ip-from-azure>
TTL: 3600
```

### Apex Domain (@):
```
# Option 1: Use ALIAS (if your DNS supports it)
Type: ALIAS
Value: smartwfm-lite.azurewebsites.net

# Option 2: Use A record (requires Azure DNS for automatic updates)
Type: A
Value: <static-ip>
```

## Security Considerations

1. **HTTPS Enforcement**: Always use HTTPS in production
2. **Domain Validation**: Use domain validation to prevent spoofing
3. **CORS Settings**: Restrict to your domain
4. **Rate Limiting**: Configure in App Service networking
5. **WAF Rules**: Consider adding Azure Web Application Firewall

## Next Steps

After successful domain integration:

1. Test accessing the app at your custom domain
2. Update marketing materials to reference new domain
3. Set up monitoring and alerts in Azure Monitor
4. Configure backup/disaster recovery
5. Monitor SSL certificate expiration dates
