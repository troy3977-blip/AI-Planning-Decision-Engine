#!/bin/bash

# Script to configure custom domain for Azure App Service
# Usage: ./setup-domain.sh <domain-name> <resource-group> <app-name>

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 1 ]; then
    echo -e "${RED}Usage: $0 <domain-name> [resource-group] [app-name]${NC}"
    echo "Example: $0 wfm.example.com my-rg smartwfm-lite"
    exit 1
fi

DOMAIN_NAME=$1
RESOURCE_GROUP=${2:-"default"}
APP_NAME=${3:-"smartwfm-lite"}

echo -e "${YELLOW}=== Azure App Service Domain Setup ===${NC}"
echo "Domain: $DOMAIN_NAME"
echo "App: $APP_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Step 1: Verify Azure login
echo -e "${YELLOW}Step 1: Verifying Azure authentication...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated${NC}"
echo ""

# Step 2: Verify resource group and app service exist
echo -e "${YELLOW}Step 2: Verifying App Service...${NC}"
if ! az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo -e "${RED}App Service '$APP_NAME' not found in resource group '$RESOURCE_GROUP'${NC}"
    exit 1
fi
echo -e "${GREEN}✓ App Service found${NC}"

# Get app service details
APP_URL=$(az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query 'defaultHostName' -o tsv)
APP_IP=$(az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query 'outboundIpAddresses' -o tsv)
echo "App URL: $APP_URL"
echo "Outbound IPs: $APP_IP"
echo ""

# Step 3: Add custom domain binding
echo -e "${YELLOW}Step 3: Adding custom domain binding...${NC}"
if az webapp config hostname add \
    --webapp-name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --hostname $DOMAIN_NAME 2>/dev/null; then
    echo -e "${GREEN}✓ Custom domain binding added${NC}"
else
    echo -e "${YELLOW}⚠ Domain binding may already exist${NC}"
fi
echo ""

# Step 4: Provide DNS configuration instructions
echo -e "${YELLOW}Step 4: DNS Configuration Required${NC}"
echo "Add one of the following DNS records:"
echo ""
echo "CNAME Method (Recommended for subdomains):"
echo "  Type: CNAME"
echo "  Name: $(echo $DOMAIN_NAME | cut -d. -f1)"
echo "  Value: $APP_URL"
echo "  TTL: 3600"
echo ""
echo "A Record Method (For apex domains):"
echo "  Type: A"
echo "  Name: @"
echo "  Value: (Check Azure Portal for static IP)"
echo "  TTL: 3600"
echo ""

# Step 5: Create App Service managed certificate
echo -e "${YELLOW}Step 5: Creating App Service Managed Certificate...${NC}"
if az webapp config ssl create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --hostname $DOMAIN_NAME 2>/dev/null; then
    echo -e "${GREEN}✓ Certificate created${NC}"
    sleep 5
    
    # Get certificate thumbprint
    THUMBPRINT=$(az webapp config ssl list \
        --resource-group $RESOURCE_GROUP \
        --query "[?hostNames[?contains(@, '$DOMAIN_NAME')]].thumbprint" -o tsv)
    
    if [ ! -z "$THUMBPRINT" ]; then
        echo "Certificate Thumbprint: $THUMBPRINT"
        echo ""
        
        # Step 6: Bind certificate
        echo -e "${YELLOW}Step 6: Binding SSL certificate...${NC}"
        if az webapp config ssl bind \
            --resource-group $RESOURCE_GROUP \
            --name $APP_NAME \
            --certificate-thumbprint $THUMBPRINT \
            --ssl-type SNI 2>/dev/null; then
            echo -e "${GREEN}✓ SSL certificate bound${NC}"
        else
            echo -e "${YELLOW}⚠ Certificate binding may need manual configuration${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠ Certificate creation needs manual configuration in Azure Portal${NC}"
fi
echo ""

# Step 7: Test domain
echo -e "${YELLOW}Step 7: Testing domain configuration...${NC}"
echo "Waiting 30 seconds for DNS propagation..."
sleep 30

if ping -c 1 $DOMAIN_NAME &> /dev/null; then
    echo -e "${GREEN}✓ Domain is resolvable${NC}"
else
    echo -e "${YELLOW}⚠ Domain not yet resolvable (may take 5-15 minutes)${NC}"
fi
echo ""

# Final summary
echo -e "${YELLOW}=== Setup Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Add DNS records to your registrar (see above)"
echo "2. Wait for DNS propagation (5-15 minutes)"
echo "3. Test: curl https://$DOMAIN_NAME"
echo "4. Verify in Azure Portal → App Service → Custom domains"
echo ""
echo -e "${GREEN}Your app will be accessible at: https://$DOMAIN_NAME${NC}"
