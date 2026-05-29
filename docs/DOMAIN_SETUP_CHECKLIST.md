# Custom Domain Setup Checklist

## Pre-Setup Verification
- [ ] Azure App Service deployed (`smartwfmai`)
- [ ] GitHub Actions deployment workflow running successfully
- [ ] Custom domain registered with a registrar
- [ ] Azure CLI installed locally
- [ ] Logged into Azure CLI (`az account show`)
- [ ] Have contributor access to Azure subscription

## Step-by-Step Setup Guide

### Phase 1: Preparation (10 minutes)

#### 1.1 Gather Information
```bash
# Run from repository root
cd /workspaces/AI-Planning-Decision-Engine

# Get your resource group and app details
az webapp show --name smartwfmai --query "resourceGroup" -o tsv
az webapp show --name smartwfmai --query "defaultHostName" -o tsv
```
- [ ] Note your resource group name: _______________
- [ ] Note your app hostname: _______________
- [ ] Have your domain name ready: _______________

#### 1.2 Decide DNS Method
- [ ] CNAME method (recommended for subdomains like `wfm.example.com`)
- [ ] A Record method (for apex domains like `example.com`)
- [ ] Azure DNS (managed hosting for your domain)

### Phase 2: Add Domain Binding (5 minutes)

#### 2.1 Automated Setup (Recommended)

**Linux/Mac:**
```bash
chmod +x scripts/setup-domain.sh
./scripts/setup-domain.sh your-domain.com your-resource-group smartwfmai
```
- [ ] Script completed successfully

**Windows (PowerShell):**
```powershell
.\scripts\setup-domain.ps1 -DomainName "your-domain.com" `
  -ResourceGroup "your-resource-group" `
  -AppName "smartwfmai"
```
- [ ] Script completed successfully

**GitHub Actions (Automated):**
1. Go to GitHub repo → Actions
2. Select "Setup Custom Domain" workflow
3. Click "Run workflow"
4. Enter domain name and resource group
5. Click "Run workflow"
- [ ] Workflow completed successfully

#### 2.2 Manual Setup (if automated fails)

```bash
# Add domain binding
az webapp config hostname add \
  --webapp-name smartwfmai \
  --resource-group your-resource-group \
  --hostname your-domain.com

# Create managed certificate
az webapp config ssl create \
  --name smartwfmai \
  --resource-group your-resource-group \
  --hostname your-domain.com

# Get certificate thumbprint
az webapp config ssl list \
  --resource-group your-resource-group \
  --query "[?hostNames[?contains(@, 'your-domain.com')]].thumbprint" -o tsv

# Bind certificate (replace THUMBPRINT)
az webapp config ssl bind \
  --resource-group your-resource-group \
  --name smartwfmai \
  --certificate-thumbprint THUMBPRINT \
  --ssl-type SNI
```
- [ ] All commands executed successfully

### Phase 3: DNS Configuration (varies by provider)

#### 3.1 For CNAME Method (Recommended for subdomains)

**GoDaddy:**
- [ ] Log in to GoDaddy DNS
- [ ] Add CNAME record:
  - Name: `wfm` (or your subdomain)
  - Points To: `smartwfmai.azurewebsites.net`
  - TTL: 3600

**Namecheap:**
- [ ] Log in to Namecheap
- [ ] Go to Domain List → Manage Domain
- [ ] Click DNS Settings
- [ ] Add CNAME record:
  - Host: `wfm`
  - Value: `smartwfmai.azurewebsites.net`
  - TTL: 3600

**Route53 (AWS):**
- [ ] Create CNAME record set:
  - Name: `wfm.example.com`
  - Type: CNAME
  - Value: `smartwfmai.azurewebsites.net`
  - TTL: 300

**Other providers:**
- [ ] Add CNAME record in your provider's DNS panel
- [ ] Host: Your subdomain
- [ ] Value: `smartwfmai.azurewebsites.net`

#### 3.2 For A Record Method (For apex domains)

First, get the static IP from Azure Portal:
1. Go to Azure Portal → smartwfmai → Custom domains
2. Note the IP address listed

Then add A record:
- [ ] Add A record in your DNS provider
- [ ] Host: `@` (for root domain) or `example.com`
- [ ] Value: [IP from step 1]
- [ ] TTL: 3600

### Phase 4: Verification (10-15 minutes)

#### 4.1 Wait for DNS Propagation
- [ ] Set a timer for 5-15 minutes
- [ ] DNS typically propagates within this time

#### 4.2 Verify DNS Resolution
```bash
# Check if domain resolves
nslookup your-domain.com

# Or use dig
dig your-domain.com

# Expected: Shows Azure IP or CNAME pointing to azurewebsites.net
```
- [ ] DNS resolves correctly

#### 4.3 Check Domain Binding in Azure Portal
1. Go to Azure Portal
2. App Services → smartwfmai → Custom domains
- [ ] Your domain appears in the list
- [ ] Status shows "Healthy" or "Certificate OK"

#### 4.4 Test HTTPS Access
```bash
# Test with curl
curl -v https://your-domain.com

# Or visit in browser
# https://your-domain.com
```
- [ ] App loads successfully
- [ ] No certificate warnings
- [ ] No 403/404 errors

#### 4.5 Verify SSL Certificate
- [ ] Browser shows lock icon
- [ ] Certificate is valid (not expired)
- [ ] Certificate matches domain name

### Phase 5: Security Configuration (5 minutes)

#### 5.1 Force HTTPS Redirection
```bash
az webapp update \
  --name smartwfmai \
  --resource-group your-resource-group \
  --https-only true
```
- [ ] HTTPS-only mode enabled

#### 5.2 Update App Settings for Domain
```bash
az webapp config appsettings set \
  --name smartwfmai \
  --resource-group your-resource-group \
  --settings \
    CUSTOM_DOMAIN="your-domain.com" \
    STREAMLIT_SERVER_HEADLESS="true" \
    STREAMLIT_CLIENT_SHOW_ERROR_DETAILS="false"
```
- [ ] App settings updated

#### 5.3 Configure CORS (if needed)
Update `.streamlit/config.toml` and redeploy:
```toml
[server]
enableCORS = true
allowedOrigins = ["your-domain.com", "*.example.com"]
```
- [ ] CORS configured

### Phase 6: Post-Setup Tasks

#### 6.1 Monitor Domain Health
- [ ] Set up Azure Monitor alerts
- [ ] Monitor custom domain endpoint

#### 6.2 SSL Certificate Renewal
- [ ] Verify auto-renewal is enabled (default for App Service managed certs)
- [ ] Note renewal date in Azure Portal

#### 6.3 Documentation Updates
- [ ] Update README with new domain
- [ ] Update any API documentation
- [ ] Update client/SDK references
- [ ] Notify users of new domain

#### 6.4 Testing
- [ ] Test app from different locations/devices
- [ ] Test on mobile devices
- [ ] Test with VPN/different networks
- [ ] Verify all functionality works

### Phase 7: Optional - Production Hardening

#### 7.1 Set Up WAF (Web Application Firewall)
```bash
az webapp waf-config set \
  --name smartwfmai \
  --resource-group your-resource-group \
  --enabled true \
  --mode Detection
```
- [ ] WAF enabled (optional)

#### 7.2 Configure Rate Limiting
Configure in Azure Portal or via Azure CLI
- [ ] Rate limits configured

#### 7.3 Enable Diagnostics Logging
```bash
az webapp log config \
  --name smartwfmai \
  --resource-group your-resource-group \
  --application-logging true
```
- [ ] Logging enabled

## Troubleshooting

### Domain not resolving?
```bash
# Check DNS propagation across multiple providers
dig your-domain.com @1.1.1.1
dig your-domain.com @8.8.8.8

# Clear local DNS cache
# On Windows: ipconfig /flushdns
# On Mac: sudo dscacheutil -flushcache
# On Linux: sudo systemctl restart systemd-resolved
```

### SSL Certificate Issues?
- Azure Portal → smartwfmai → TLS/SSL settings
- Look for error messages
- Try manually renewing certificate

### 403 Forbidden Error?
- Check Azure Portal → Networking → Access restrictions
- Verify domain binding is "Healthy"
- Ensure HTTPS is properly configured

### App loads but shows errors?
- Check Application Insights logs
- Review Streamlit server logs
- Verify all environment variables are set

## Quick Reference Commands

```bash
# View all custom domains
az webapp hostname list --name smartwfmai --resource-group your-resource-group

# Remove a custom domain
az webapp config hostname delete \
  --webapp-name smartwfmai \
  --resource-group your-resource-group \
  --hostname your-domain.com

# List SSL certificates
az webapp config ssl list --resource-group your-resource-group

# Check domain binding status
az webapp config hostname show \
  --name smartwfmai \
  --resource-group your-resource-group \
  --hostname your-domain.com
```

## Success Indicators

✅ All of the following should be true:
- [ ] App loads at `https://your-domain.com`
- [ ] No certificate warnings in browser
- [ ] Domain shows "Healthy" in Azure Portal
- [ ] HTTPS enforced
- [ ] App functionality works normally
- [ ] No console errors in browser DevTools

---

**Setup Date:** _______________
**Domain:** _______________
**Completed By:** _______________
**Notes:** _______________
