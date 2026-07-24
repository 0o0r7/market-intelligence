param ( [Parameter(Mandatory=$true)][string]$AppName, [Parameter(Mandatory=$true)][string]$ResourceGroupName, [Parameter(Mandatory=$true)][string]$CoinglassApiKey, [string]$Location = "eastus" )
Write-Host "Logging into Azure..." -ForegroundColor Cyan
az login
Write-Host "Creating Resource Group: $ResourceGroupName..." -ForegroundColor Cyan
az group create --name $ResourceGroupName --location $Location
Write-Host "Deploying Azure Infrastructure..." -ForegroundColor Cyan
$deployment = az deployment group create --resource-group $ResourceGroupName --template-file "$PSScriptRoot\..\azuredeploy.bicep" --parameters appName=$AppName coinglassApiKey=$CoinglassApiKey --output json | ConvertFrom-Json
Write-Host "Deployment Complete." -ForegroundColor Green
Write-Host "Function App Name: $($deployment.properties.outputs.functionAppName.value)"
Write-Host "Key Vault Name: $($deployment.properties.outputs.keyVaultName.value)"
$storageAccountName = "$($AppName.ToLower())st$($deployment.properties.outputs.uniqueSuffix.value)"
Write-Host "Creating 'charts' blob container..." -ForegroundColor Cyan
az storage container create --name charts --account-name $storageAccountName --auth-mode login
Write-Host "Infrastructure deployment successful." -ForegroundColor Green