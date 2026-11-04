<#
.SYNOPSIS
  Seeds the DynamoDB table using AWS CLI batch-write-item.
#>

param(
    [string]$TableName = "ServerlessResumeTable",
    [string]$Region = "us-east-1"
)

Write-Host "Seeding table '$TableName' in $Region using batch-write-item..." -ForegroundColor Cyan

# Replace placeholder table name in temp json if needed
$jsonContent = Get-Content -Raw "scripts/seed_dynamodb_items.json"
if ($TableName -ne "ServerlessResumeTable") {
    $jsonContent = $jsonContent -replace '"ServerlessResumeTable"', "`"$TableName`""
}
$tempFile = [System.IO.Path]::GetTempFileName()
Set-Content -Path $tempFile -Value $jsonContent

aws dynamodb batch-write-item --request-items "file://$tempFile" --region $Region

Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue

Write-Host "Batch write complete!" -ForegroundColor Green
