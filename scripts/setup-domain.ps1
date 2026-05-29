# PowerShell script to configure custom domain for Azure App Service
# Usage: .\setup-domain.ps1 -DomainName "wfm.example.com" -ResourceGroup "my-rg" -AppName "smartwfmai"

param (
    [Parameter(Mandatory=$true)]
    [string]$DomainName,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "default",
    
    [Parameter(Mandatory=$false)]
    [string]$AppName = "smartwfmai"
)

# Color output helper
function Write-ColorOutput($color, $message) {
    Write-Host $message -ForegroundColor $color
}

Write-ColorOutput "Yellow" "=== Azure App Service Domain Setup ==="
Write-ColorOutput "Cyan" "Domain: $DomainName"
Write-ColorOutput "Cyan" "App: $AppName"
Write-ColorOutput "Cyan" "Resource Group: $ResourceGroup"
Write-Host ""

# Step 1: Verify Azure login
Write-ColorOutput "Yellow" "Step 1: Verifying Azure authentication..."
try {
    $account = az account show | ConvertFrom-Json
    Write-ColorOutput "Green" "✓ Authenticated as: $($account.user.name)"
} catch {
    Write-ColorOutput "Red" "Not logged in to Azure. Please run 'az login' first."
    exit 1
}
Write-Host ""

# Step 2: Verify resource group and app service exist
Write-ColorOutput "Yellow" "Step 2: Verifying App Service..."
try {
    $appService = az webapp show --name $AppName --resource-group $ResourceGroup | ConvertFrom-Json
    Write-ColorOutput "Green" "✓ App Service found"
    Write-ColorOutput "Cyan" "App URL: $($appService.defaultHostName)"
    Write-ColorOutput "Cyan" "Outbound IPs: $($appService.outboundIpAddresses)"
} catch {
    Write-ColorOutput "Red" "App Service '$AppName' not found in resource group '$ResourceGroup'"
    exit 1
}
Write-Host ""

# Step 3: Add custom domain binding
Write-ColorOutput "Yellow" "Step 3: Adding custom domain binding..."
try {
    az webapp config hostname add `
        --webapp-name $AppName `
        --resource-group $ResourceGroup `
        --hostname $DomainName
    Write-ColorOutput "Green" "✓ Custom domain binding added"
} catch {
    Write-ColorOutput "Yellow" "⚠ Domain binding may already exist"
}
Write-Host ""

# Step 4: Provide DNS configuration instructions
Write-ColorOutput "Yellow" "Step 4: DNS Configuration Required"
$subdomain = $DomainName.Split('.')[0]
Write-ColorOutput "Cyan" "Add one of the following DNS records:"
Write-Host ""
Write-ColorOutput "Cyan" "CNAME Method (Recommended for subdomains):"
Write-Host "  Type: CNAME"
Write-Host "  Name: $subdomain"
Write-Host "  Value: $($appService.defaultHostName)"
Write-Host "  TTL: 3600"
Write-Host ""
Write-ColorOutput "Cyan" "A Record Method (For apex domains):"
Write-Host "  Type: A"
Write-Host "  Name: @"
Write-Host "  Value: (Check Azure Portal for static IP)"
Write-Host "  TTL: 3600"
Write-Host ""

# Step 5: Create App Service managed certificate
Write-ColorOutput "Yellow" "Step 5: Creating App Service Managed Certificate..."
try {
    az webapp config ssl create `
        --name $AppName `
        --resource-group $ResourceGroup `
        --hostname $DomainName
    Write-ColorOutput "Green" "✓ Certificate created"
    Write-Host "Waiting 5 seconds..."
    Start-Sleep -Seconds 5
    
    # Get certificate thumbprint
    $certificateInfo = az webapp config ssl list `
        --resource-group $ResourceGroup `
        --query "[?hostNames[?contains(@, '$DomainName')]]" | ConvertFrom-Json
    
    if ($certificateInfo) {
        $thumbprint = $certificateInfo[0].thumbprint
        Write-ColorOutput "Cyan" "Certificate Thumbprint: $thumbprint"
        Write-Host ""
        
        # Step 6: Bind certificate
        Write-ColorOutput "Yellow" "Step 6: Binding SSL certificate..."
        try {
            az webapp config ssl bind `
                --resource-group $ResourceGroup `
                --name $AppName `
                --certificate-thumbprint $thumbprint `
                --ssl-type SNI
            Write-ColorOutput "Green" "✓ SSL certificate bound"
        } catch {
            Write-ColorOutput "Yellow" "⚠ Certificate binding may need manual configuration"
        }
    }
} catch {
    Write-ColorOutput "Yellow" "⚠ Certificate creation needs manual configuration in Azure Portal"
}
Write-Host ""

# Step 7: Test domain
Write-ColorOutput "Yellow" "Step 7: Testing domain configuration..."
Write-Host "Waiting 30 seconds for DNS propagation..."
Start-Sleep -Seconds 30

try {
    $result = [System.Net.Dns]::GetHostAddresses($DomainName)
    Write-ColorOutput "Green" "✓ Domain is resolvable"
} catch {
    Write-ColorOutput "Yellow" "⚠ Domain not yet resolvable (may take 5-15 minutes)"
}
Write-Host ""

# Final summary
Write-ColorOutput "Yellow" "=== Setup Complete ==="
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Add DNS records to your registrar (see above)"
Write-Host "2. Wait for DNS propagation (5-15 minutes)"
Write-Host "3. Test: Invoke-WebRequest https://$DomainName"
Write-Host "4. Verify in Azure Portal → App Service → Custom domains"
Write-Host ""
Write-ColorOutput "Green" "Your app will be accessible at: https://$DomainName"
