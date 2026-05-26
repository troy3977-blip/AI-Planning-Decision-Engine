# DNS Configuration Record

## Project Information
- **Project**: SmartWFM Lite
- **App Service Name**: smartwfm-lite
- **Azure Region**: [Your Region]
- **Resource Group**: [Your Resource Group]
- **Domain Name**: [Your Domain]
- **Setup Date**: [Date]

## DNS Provider Information
- **Provider**: [e.g., GoDaddy, Namecheap, Route53, Azure DNS]
- **Account**: [Your Account Email]
- **Status**: [ ] Active [ ] Pending [ ] Completed

## Azure App Service Details
```
Default Hostname: smartwfm-lite.azurewebsites.net
App Service URL: https://smartwfm-lite.azurewebsites.net
Custom Domain: https://[Your Domain]
```

## DNS Records Configuration

### Primary Domain Setup

#### Option A: CNAME Record (For Subdomains - Recommended)

```
Type:   CNAME
Host:   wfm (or your subdomain)
Value:  smartwfm-lite.azurewebsites.net
TTL:    3600
Status: [ ] Added [ ] Pending [ ] Verified
```

**Instructions for Different Providers:**

**GoDaddy:**
1. Log in to GoDaddy account
2. Go to Domains → Your Domain → DNS
3. Find CNAME section
4. Add Record:
   - Name: `wfm`
   - Value: `smartwfm-lite.azurewebsites.net`
   - TTL: 3600
5. Save

**Namecheap:**
1. Log in to Namecheap
2. Go to Manage Domain
3. Click Advanced DNS
4. Add New Record:
   - Type: CNAME Record
   - Host: `wfm`
   - Value: `smartwfm-lite.azurewebsites.net`
   - TTL: 3600 (Automatic)
5. Save

**Route53 (AWS):**
1. Log in to AWS Console
2. Go to Route 53 → Hosted Zones → Your Domain
3. Create Record:
   - Record name: `wfm.yourdomain.com`
   - Record type: CNAME
   - Value: `smartwfm-lite.azurewebsites.net`
   - TTL: 300
4. Create Record

**Azure DNS:**
1. Go to Azure Portal
2. DNS Zones → Your Domain
3. Record Sets → + Add
4. Create CNAME:
   - Name: `wfm`
   - Type: CNAME
   - Alias: `smartwfm-lite.azurewebsites.net`
5. OK

---

#### Option B: A Record (For Apex/Root Domain)

First, obtain static IP from Azure Portal:
- Path: App Services → smartwfm-lite → Custom domains
- Copy the IP address shown

```
Type:   A
Host:   @ (for root domain or example.com)
Value:  [IP Address from Azure]
TTL:    3600
Status: [ ] Added [ ] Pending [ ] Verified
```

**Instructions:**

**GoDaddy:**
1. Go to Domains → Your Domain → DNS
2. Find A section
3. Edit or Create:
   - Points To: [Azure IP]
   - TTL: 3600

**Namecheap:**
1. Go to Advanced DNS
2. Add A Record:
   - Host: `@`
   - Value: [Azure IP]
   - TTL: 3600 (Automatic)

---

### Optional: WWW Subdomain

If you want `www.yourdomain.com` to also work:

```
Type:   CNAME
Host:   www
Value:  smartwfm-lite.azurewebsites.net
TTL:    3600
Status: [ ] Added [ ] Pending [ ] Verified
```

---

### Optional: Domain Verification (Azure Verification)

Azure may require domain verification:

```
Type:   TXT
Host:   [Provided by Azure]
Value:  [Verification string from Azure]
TTL:    3600
Status: [ ] Added [ ] Verified
```

---

## SSL/TLS Certificate Information

```
Certificate Type:  App Service Managed Certificate
Domain:            [Your Domain]
Issuer:            Microsoft Azure TLS
Thumbprint:        [Certificate Thumbprint]
Created Date:      [Date]
Renewal Date:      Automatic (usually ~30 days before expiry)
Status:            [ ] Active [ ] Pending [ ] Expired
```

---

## DNS Propagation Verification

### Verification Commands

```bash
# Check CNAME resolution
nslookup wfm.yourdomain.com
# Expected Output: nslookup wfm.yourdomain.com
# Server: [DNS Server]
# Address: [IP]
# wfm.yourdomain.com canonical name = smartwfm-lite.azurewebsites.net

# Check with dig
dig wfm.yourdomain.com
# Expected: CNAME record pointing to smartwfm-lite.azurewebsites.net

# Check A record (if using A record method)
nslookup yourdomain.com
# Expected: Shows Azure IP address

# Check from different DNS servers
dig wfm.yourdomain.com @1.1.1.1
dig wfm.yourdomain.com @8.8.8.8
```

### Propagation Status

- [ ] DNS resolves locally
- [ ] DNS resolves from public DNS (1.1.1.1, 8.8.8.8)
- [ ] Azure Portal shows "Healthy"
- [ ] HTTPS works without warnings

**Propagation Timeline:**
- Typically: 5-15 minutes
- Maximum: 48 hours (worst case)
- Check time: [Time Checked]
- Propagation complete: [Time]

---

## Health Checks

### Daily Health Check

```bash
# Quick status check
curl -I https://yourdomain.com

# Monitor with script
while true; do
  status=$(curl -s -o /dev/null -w "%{http_code}" https://yourdomain.com)
  echo "[$(date)] Status: $status"
  sleep 300
done
```

Status Checklist:
- [ ] HTTP 200 response
- [ ] HTTPS protocol working
- [ ] No certificate warnings
- [ ] App responds in < 2 seconds
- [ ] Custom domain in browser URL bar

---

## Troubleshooting Log

| Date | Issue | Solution | Status |
|------|-------|----------|--------|
| [Date] | [Issue Description] | [Solution Applied] | [Resolved] |
| | | | |
| | | | |

---

## References

- Azure App Service Custom Domain Docs: https://learn.microsoft.com/en-us/azure/app-service/app-service-web-tutorial-custom-domain
- DNS Configuration Guide: [Repo Path]/docs/DOMAIN_INTEGRATION.md
- Setup Checklist: [Repo Path]/docs/DOMAIN_SETUP_CHECKLIST.md

---

## Sign-Off

- **Setup Completed By**: _______________
- **Date Completed**: _______________
- **Verified By**: _______________
- **Date Verified**: _______________
- **Notes**: _______________________________________________________________
