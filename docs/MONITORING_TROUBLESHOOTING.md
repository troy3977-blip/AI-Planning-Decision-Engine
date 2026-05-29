# Domain Monitoring & Troubleshooting Guide

## Monitoring Your Custom Domain

### 1. Daily Health Check

#### Quick Command Check
```bash
#!/bin/bash
# Health check script

DOMAIN="your-domain.com"
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"  # Optional Slack notification

check_domain() {
    status=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN")
    response_time=$(curl -s -o /dev/null -w "%{time_total}" "https://$DOMAIN")
    
    if [ "$status" = "200" ]; then
        echo "✓ $DOMAIN is healthy (HTTP $status, ${response_time}s)"
        return 0
    else
        echo "✗ $DOMAIN returned HTTP $status"
        return 1
    fi
}

check_ssl() {
    echo "Checking SSL certificate..."
    echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | \
        openssl x509 -noout -dates -subject
}

check_dns() {
    echo "Checking DNS resolution..."
    nslookup "$DOMAIN"
}

echo "=== Health Check for $DOMAIN ==="
echo "Time: $(date)"
echo ""

check_domain
check_ssl
check_dns
```

#### Using Online Tools
- **SSL Labs**: https://www.ssllabs.com/ssltest/ (enter your domain)
- **DNS Checker**: https://mxtoolbox.com/
- **HTTP Status Code Checker**: https://httpstatus.io/

### 2. Set Up Azure Monitor Alerts

```bash
# Create alert for app service health
az monitor metrics alert create \
  --name "Custom Domain Health Alert" \
  --resource-group your-resource-group \
  --scopes "/subscriptions/{subId}/resourceGroups/{rgName}/providers/Microsoft.Web/sites/smartwfmai" \
  --condition "avg HttpQueueLength > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --description "Alert if queue length is high"
```

### 3. Monitor SSL Certificate Expiration

```bash
# Check certificate expiration
az webapp config ssl list \
  --resource-group your-resource-group \
  --query "[?hostNames[?contains(@, 'your-domain')]].{Domain:hostNames, Thumbprint:thumbprint, Status:certificateStatus, ExpirationDate:expirationDate}" \
  --output table

# Get expiration date for specific domain
EXPIRY=$(az webapp config ssl list \
  --resource-group your-resource-group \
  --query "[?hostNames[?contains(@, 'your-domain')]].expirationDate" -o tsv)

echo "Certificate expires: $EXPIRY"
```

**Note**: App Service Managed Certificates auto-renew 30 days before expiration.

---

## Troubleshooting Guide

### Problem: Domain Not Resolving

**Symptoms:**
- `nslookup your-domain.com` returns "Non-existent domain"
- Browser shows "Could not find the server"
- Ping returns "Unknown host"

**Diagnosis:**
```bash
# Check if domain is registered and active
whois your-domain.com

# Check nameserver configuration
nslookup -type=NS your-domain.com

# Check all DNS records
dig your-domain.com ANY

# Check with different DNS servers
dig your-domain.com @1.1.1.1
dig your-domain.com @8.8.8.8
```

**Solutions:**
1. **DNS hasn't propagated yet**
   - Wait 5-15 minutes (up to 48 hours)
   - Use online tool: https://www.whatsmydns.net/

2. **DNS record is incorrect**
   - Verify CNAME/A record in your DNS provider
   - Expected: `wfm CNAME smartwfmai.azurewebsites.net`
   - Or: `@ A 20.185.X.X` (Azure IP)

3. **Nameservers not configured**
   - Check domain registrar
   - Verify nameservers match DNS provider
   - May need to update nameservers if using external DNS

4. **Recent DNS change**
   - Clear DNS cache:
     ```bash
     # Windows
     ipconfig /flushdns
     
     # macOS
     sudo dscacheutil -flushcache
     
     # Linux
     sudo systemctl restart systemd-resolved
     ```

---

### Problem: SSL Certificate Error

**Symptoms:**
- Browser shows "Your connection is not private"
- "Certificate doesn't match domain name"
- "NET::ERR_CERT_AUTHORITY_INVALID"

**Diagnosis:**
```bash
# Check SSL certificate details
echo | openssl s_client -servername your-domain.com \
  -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -text

# Check certificate expiration
echo | openssl s_client -servername your-domain.com \
  -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates

# Verify certificate matches domain
openssl s_client -servername your-domain.com \
  -connect your-domain.com:443 </dev/null 2>/dev/null | \
  openssl x509 -noout -subject -issuer
```

**Solutions:**

1. **Certificate not bound to domain**
   - Check Azure Portal: App Services → smartwfmai → Custom domains
   - Verify domain shows status "Healthy" or "Certificate OK"
   - If status is "Incomplete", restart domain binding process:
     ```bash
     # Remove and re-add domain
     az webapp config hostname delete \
       --webapp-name smartwfmai \
       --resource-group your-resource-group \
       --hostname your-domain.com
     
     az webapp config hostname add \
       --webapp-name smartwfmai \
       --resource-group your-resource-group \
       --hostname your-domain.com
     ```

2. **Certificate thumbprint mismatch**
   - Get correct thumbprint:
     ```bash
     THUMBPRINT=$(az webapp config ssl list \
       --resource-group your-resource-group \
       --query "[?hostNames[?contains(@, 'your-domain')]].thumbprint" -o tsv)
     ```
   - Re-bind certificate:
     ```bash
     az webapp config ssl bind \
       --resource-group your-resource-group \
       --name smartwfmai \
       --certificate-thumbprint $THUMBPRINT \
       --ssl-type SNI
     ```

3. **Certificate expired**
   - Check expiration: `az webapp config ssl list --resource-group your-resource-group`
   - App Service Managed Certificates auto-renew
   - If not renewed, manually:
     ```bash
     az webapp config ssl create \
       --name smartwfmai \
       --resource-group your-resource-group \
       --hostname your-domain.com
     ```

4. **Mixed content warnings**
   - Ensure HTTPS-only mode is enabled:
     ```bash
     az webapp update \
       --name smartwfmai \
       --resource-group your-resource-group \
       --https-only true
     ```

---

### Problem: 403 Forbidden / 404 Not Found

**Symptoms:**
- HTTPS works, but page shows 403 or 404
- App doesn't load on custom domain
- Works on `smartwfmai.azurewebsites.net` but not custom domain

**Diagnosis:**
```bash
# Check domain binding status
az webapp config hostname show \
  --webapp-name smartwfmai \
  --resource-group your-resource-group \
  --hostname your-domain.com

# Check IP restrictions
az webapp config access-restriction show \
  --name smartwfmai \
  --resource-group your-resource-group

# Check Streamlit logs
az webapp log tail --name smartwfmai --resource-group your-resource-group
```

**Solutions:**

1. **Domain not in allowed origins**
   - Update `.streamlit/config.toml`:
     ```toml
     [server]
     allowedOrigins = ["your-domain.com", "*.yourdomain.com", "smartwfmai.azurewebsites.net"]
     ```
   - Redeploy app

2. **CORS misconfiguration**
   - Check CORS settings:
     ```bash
     az resource show --name smartwfmai \
       --resource-group your-resource-group \
       --resource-type "Microsoft.Web/sites" \
       --query "properties.cors"
     ```

3. **IP restriction blocking domain**
   - Check if IP restrictions are enabled:
     ```bash
     az webapp config access-restriction list \
       --name smartwfmai \
       --resource-group your-resource-group
     ```
   - Remove restrictions if too strict:
     ```bash
     az webapp config access-restriction remove \
       --name smartwfmai \
       --resource-group your-resource-group \
       --rule-name "Allow all" # or specific rule name
     ```

---

### Problem: HTTPS Not Enforced

**Symptoms:**
- HTTP (not HTTPS) works
- Browser doesn't auto-redirect to HTTPS
- Insecure content warnings

**Solution:**
```bash
# Force HTTPS-only
az webapp update \
  --name smartwfmai \
  --resource-group your-resource-group \
  --https-only true

# Verify
az webapp show \
  --name smartwfmai \
  --resource-group your-resource-group \
  --query "httpsOnly"
```

---

### Problem: App Slow or Timing Out

**Symptoms:**
- Pages load slowly
- Timeout errors
- 504 Bad Gateway

**Diagnosis:**
```bash
# Test response time
time curl -I https://your-domain.com

# Check app service metrics
az monitor metrics list \
  --resource /subscriptions/{subId}/resourceGroups/{rgName}/providers/Microsoft.Web/sites/smartwfmai \
  --metric "ResponseTime" \
  --start-time 2024-01-01T00:00:00 \
  --end-time 2024-01-02T00:00:00
```

**Solutions:**

1. **Scale up app service plan**
   ```bash
   az appservice plan update \
     --name your-plan \
     --resource-group your-resource-group \
     --sku S1  # Scale up from B1 to S1
   ```

2. **Check for errors**
   ```bash
   az webapp log tail --name smartwfmai \
     --resource-group your-resource-group
   ```

3. **Monitor resource usage**
   - Azure Portal → smartwfmai → Metrics
   - Check CPU, Memory, Network

---

## Performance Optimization

### 1. Enable Caching
```toml
# .streamlit/config.toml
[cache]
maxMsgCacheEntrySize = 2
```

### 2. Optimize Images
```python
# In ui/app.py
st.set_page_config(
    page_title="SmartWFM",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### 3. Use Connection Pooling
```python
# For database connections (if applicable)
import streamlit as st

@st.cache_resource
def get_database_connection():
    # Return pooled connection
    pass
```

---

## Recovery Procedures

### Restart App Service
```bash
az webapp restart \
  --name smartwfmai \
  --resource-group your-resource-group
```

### Redeploy Application
```bash
# Trigger GitHub Actions deployment
git push origin main

# Or manual deployment
az webapp deployment source config-zip \
  --resource-group your-resource-group \
  --name smartwfmai \
  --src-path ./app.zip
```

### Rollback to Previous Version
```bash
# List deployment slots
az webapp deployment slot list \
  --name smartwfmai \
  --resource-group your-resource-group

# Swap to previous slot
az webapp deployment slot swap \
  --name smartwfmai \
  --resource-group your-resource-group \
  --slot staging
```

---

## Incident Response Checklist

When domain issues occur:

- [ ] Check domain DNS resolution (`nslookup`, `dig`)
- [ ] Verify Azure App Service status (Azure Portal)
- [ ] Check SSL certificate status and expiration
- [ ] Review recent changes/deployments
- [ ] Check Azure Monitor alerts
- [ ] Review application logs
- [ ] Test from different networks/locations
- [ ] Clear browser cache and DNS cache
- [ ] Check firewall/security group rules
- [ ] Contact Azure Support if infrastructure issue
- [ ] Contact DNS provider if DNS issue

---

## Quick Command Reference

```bash
# Test domain
curl -I https://your-domain.com
curl -v https://your-domain.com

# Check DNS
nslookup your-domain.com
dig your-domain.com

# Check SSL
echo | openssl s_client -connect your-domain.com:443
openssl s_client -servername your-domain.com -connect your-domain.com:443

# Check App Service
az webapp show --name smartwfmai --resource-group your-resource-group

# View logs
az webapp log tail --name smartwfmai --resource-group your-resource-group

# Restart app
az webapp restart --name smartwfmai --resource-group your-resource-group

# Update settings
az webapp config appsettings set --name smartwfmai --resource-group your-resource-group --settings KEY=VALUE
```

---

## Support Resources

- [Azure App Service Documentation](https://learn.microsoft.com/en-us/azure/app-service/)
- [Custom Domain Setup Guide](https://learn.microsoft.com/en-us/azure/app-service/app-service-web-tutorial-custom-domain)
- [SSL/TLS Certificate Management](https://learn.microsoft.com/en-us/azure/app-service/configure-ssl-certificate)
- [Streamlit Documentation](https://docs.streamlit.io)
- [DNS Propagation Checker](https://www.whatsmydns.net/)
- [SSL Certificate Checker](https://www.ssllabs.com/ssltest/)
