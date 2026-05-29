param location string = resourceGroup().location
param appServiceName string = 'smartwfmai'
param customDomainName string = ''
param certificateThumbprint string = ''
param environment string = 'production'

// Existing App Service reference
resource appService 'Microsoft.Web/sites@2023-12-01' existing = {
  name: appServiceName
}

// Add custom domain binding
resource customDomain 'Microsoft.Web/sites/hostNameBindings@2023-12-01' = if (customDomainName != '') {
  parent: appService
  name: customDomainName
  properties: {
    siteName: appServiceName
    hostNameType: 'Verified'
  }
}

// SSL Certificate binding (if using App Service Managed Certificate)
resource sslBinding 'Microsoft.Web/sites/hostNameBindings@2023-12-01' = if (certificateThumbprint != '') {
  parent: appService
  name: customDomainName
  properties: {
    siteName: appServiceName
    hostNameType: 'Verified'
    sslState: 'SniEnabled'
    thumbprint: certificateThumbprint
  }
}

// Update web config for HTTPS redirection
resource webConfig 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: appService
  name: 'web'
  properties: {
    numberOfWorkers: 1
    defaultDocuments: []
    netFrameworkVersion: 'v7.0'
    requestTracingEnabled: false
    remoteDebuggingEnabled: false
    httpLoggingEnabled: true
    detailedErrorLoggingEnabled: true
    publishingUsername: appServiceName
    scmType: 'GitHub'
    use32BitWorkerProcess: false
    webSocketsEnabled: true
    managedPipelineMode: 'Integrated'
    virtualApplications: [
      {
        virtualPath: '/'
        physicalPath: 'site\\wwwroot'
        preloadEnabled: false
      }
    ]
    loadBalancing: 'LeastRequests'
    experiments: {
      rampUpRules: []
    }
    autoHealEnabled: false
    localMySqlEnabled: false
    cors: {
      allowedOrigins: [
        '*'
      ]
      supportCredentials: false
    }
    localCacheEnabled: false
    ipSecurityRestrictions: [
      {
        ipAddress: 'Any'
        action: 'Allow'
        priority: 2147483647
        name: 'Allow all'
        description: 'Allow all access'
      }
    ]
    scmIpSecurityRestrictions: [
      {
        ipAddress: 'Any'
        action: 'Allow'
        priority: 2147483647
        name: 'Allow all'
        description: 'Allow all access'
      }
    ]
    scmIpSecurityRestrictionsUseMain: false
    http20Enabled: true
    minTlsVersion: '1.2'
    scmMinTlsVersion: '1.0'
    ftpsState: 'FtpsOnly'
    preWarmedInstanceCount: 0
    functionAppScaleLimit: 0
    fileChangeAuditEnabled: false
    functionsRuntimeScaleMonitoringEnabled: false
    websiteTimeZone: 'UTC'
    minimumElasticInstanceCount: 1
    azureStorageAccounts: {}
    machineKey: {
      validationKey: ''
      decryptionKey: ''
    }
    sessionAffinity: 'Off'
  }
}

// App Service settings for custom domain
resource appSettings 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: appService
  name: 'appsettings'
  properties: {
    STREAMLIT_SERVER_HEADLESS: 'true'
    STREAMLIT_SERVER_PORT: '8501'
    STREAMLIT_SERVER_ADDRESS: '0.0.0.0'
    STREAMLIT_CLIENT_SHOW_ERROR_DETAILS: 'false'
    CUSTOM_DOMAIN: customDomainName
    ENVIRONMENT: environment
    WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'
  }
}

output appServiceName string = appService.name
output customDomainName string = customDomainName
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output customDomainUrl string = customDomainName != '' ? 'https://${customDomainName}' : ''
