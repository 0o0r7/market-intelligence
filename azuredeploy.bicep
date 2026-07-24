param appName string
param location string = resourceGroup().location
param coinglassApiKey string
param repoUrl string = ''

var storageAccountName = toLower('st')
var functionAppName = '-func'
var keyVaultName = '-kv'
var appInsightsName = '-ai'
var serverFarmName = '-asp'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName; location: location; sku: { name: 'Standard_LRS' }; kind: 'StorageV2'
  properties: { supportsHttpsTrafficOnly: true; minimumTlsVersion: 'TLS1_2' }
}

resource serverFarm 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: serverFarmName; location: location; sku: { name: 'FC1', tier: 'FlexConsumption' }
  properties: { reserved: true }
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName; location: location; kind: 'functionapp,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: serverFarm.id
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        { name: 'AzureWebJobsStorage__accountName', value: storageAccountName }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'FUNCTIONS_WORKER_RUNTIME_VERSION', value: '3.11' }
        { name: 'ENVIRONMENT', value: 'production' }
        { name: 'COINGLASS_API_KEY', value: '@Microsoft.KeyVault(VaultName=;SecretName=COINGLASS-API-KEY)' }
        { name: 'KEY_VAULT_URL', value: 'https://.vault.azure.net/' }
        { name: 'AZURE_STORAGE_CONNECTION_STRING', value: '@Microsoft.KeyVault(VaultName=;SecretName=STORAGE-CONNECTION-STRING)' }
        { name: 'CHART_CONTAINER_NAME', value: 'charts' }
      ]
      ftpsState: 'Disabled'; minTlsVersion: '1.2'
    }
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName; location: location
  properties: {
    sku: { family: 'A', name: 'standard' }; tenantId: functionApp.identity.tenantId
    accessPolicies: [
      {
        tenantId: functionApp.identity.tenantId; objectId: functionApp.identity.principalId
        permissions: { secrets: [ 'get', 'list' ] }
      }
    ]
    enableRbacAuthorization: false
  }
}

resource coinglassSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault; name: 'COINGLASS-API-KEY'; properties: { value: coinglassApiKey }
}

resource storageConnectionString 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: keyVault; name: 'STORAGE-CONNECTION-STRING'
  properties: { value: 'DefaultEndpointsProtocol=https;AccountName=;AccountKey=;EndpointSuffix=core.windows.net' }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName; location: location; kind: 'web'
  properties: { Application_Type: 'web', Request_Source: 'rest' }
}

resource appInsightsSetting 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: functionApp; name: 'appsettings'
  properties: {
    APPINSIGHTS_INSTRUMENTATIONKEY: appInsights.properties.InstrumentationKey
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
  }
}

output functionAppName string = functionApp.name
output functionAppIdentity string = functionApp.identity.principalId
output keyVaultName string = keyVault.name