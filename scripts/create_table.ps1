<#
.SYNOPSIS
  Creates the Amazon DynamoDB table for the Serverless Resume API using AWS CLI.

.DESCRIPTION
  Creates 'ServerlessResumeTable' with composite primary key:
    Partition Key: PK (String)
    Sort Key:      SK (String)
  Configured with On-Demand billing (PAY_PER_REQUEST).
#>

param(
    [string]$TableName = "ServerlessResumeTable",
    [string]$Region = "us-east-1"
)

Write-Host "Creating DynamoDB Table: $TableName in region $Region..." -ForegroundColor Cyan

aws dynamodb create-table `
    --table-name $TableName `
    --attribute-definitions `
        AttributeName=PK,AttributeType=S `
        AttributeName=SK,AttributeType=S `
    --key-schema `
        AttributeName=PK,KeyType=HASH `
        AttributeName=SK,KeyType=RANGE `
    --billing-mode PAY_PER_REQUEST `
    --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "Waiting for table to become ACTIVE..." -ForegroundColor Yellow
    aws dynamodb wait table-exists --table-name $TableName --region $Region
    Write-Host "Table '$TableName' is now ACTIVE and ready to use!" -ForegroundColor Green
} else {
    Write-Host "Failed to create table or table already exists." -ForegroundColor Red
}
