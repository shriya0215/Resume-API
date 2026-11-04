<#
.SYNOPSIS
  Deploys the Serverless Resume API to AWS using AWS SAM CLI.

.DESCRIPTION
  Builds, packages, and deploys the CloudFormation stack, then retrieves
  the API Gateway URL and API Key for testing.
#>

param(
    [string]$StackName = "serverless-resume-api",
    [string]$Region = "us-east-1",
    [string]$Stage = "prod"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Building and Deploying Serverless Resume API with AWS SAM" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Build SAM Application
Write-Host "`n[1/3] Building SAM application..." -ForegroundColor Yellow
sam build

if ($LASTEXITCODE -ne 0) {
    Write-Host "SAM build failed. Please ensure Docker or Python is installed." -ForegroundColor Red
    exit 1
}

# 2. Deploy SAM Application
Write-Host "`n[2/3] Deploying CloudFormation stack: $StackName ($Region)..." -ForegroundColor Yellow
sam deploy `
    --stack-name $StackName `
    --region $Region `
    --capabilities CAPABILITY_IAM `
    --resolve-s3 `
    --parameter-overrides StageName=$Stage `
    --no-confirm-changeset

if ($LASTEXITCODE -ne 0) {
    Write-Host "SAM deploy failed." -ForegroundColor Red
    exit 1
}

# 3. Retrieve Outputs
Write-Host "`n[3/3] Retrieving API Gateway URL and API Key..." -ForegroundColor Green

$outputs = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --region $Region `
    --query "Stacks[0].Outputs" `
    --output json | ConvertFrom-Json

$apiUrl = ($outputs | Where-Object { $_.OutputKey -eq "ApiUrl" }).OutputValue
$apiKeyId = ($outputs | Where-Object { $_.OutputKey -eq "ApiKeyId" }).OutputValue

if ($apiKeyId) {
    $apiKeyValObj = aws apigateway get-api-key `
        --api-key $apiKeyId `
        --include-value `
        --region $Region `
        --output json | ConvertFrom-Json
    $apiKeyValue = $apiKeyValObj.value
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Base API Endpoint: $apiUrl"
Write-Host "API Key ID:        $apiKeyId"
Write-Host "API Key Value:     $apiKeyValue"
Write-Host "`nExample cURL Commands for Testing:"
Write-Host "----------------------------------------------------------"
Write-Host "curl -H `"x-api-key: $apiKeyValue`" `"${apiUrl}personal`""
Write-Host "curl -H `"x-api-key: $apiKeyValue`" `"${apiUrl}experience`""
Write-Host "curl -H `"x-api-key: $apiKeyValue`" `"${apiUrl}education`""
Write-Host "curl -H `"x-api-key: $apiKeyValue`" `"${apiUrl}skills`""
Write-Host "curl `"${apiUrl}health`"   (Public health check)"
Write-Host "==========================================================`n"
