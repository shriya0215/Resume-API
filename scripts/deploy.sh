#!/usr/bin/env bash
# ==============================================================================
# Automated Deployment Script for Serverless Resume API via AWS SAM
# ==============================================================================

set -euo pipefail

STACK_NAME="${1:-serverless-resume-api}"
REGION="${2:-us-east-1}"
STAGE="${3:-prod}"

echo "=========================================================="
echo " Building and Deploying Serverless Resume API with AWS SAM"
echo "=========================================================="

echo -e "\n[1/3] Building SAM application..."
sam build

echo -e "\n[2/3] Deploying CloudFormation stack: ${STACK_NAME} (${REGION})..."
sam deploy \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --parameter-overrides StageName="${STAGE}" \
    --no-confirm-changeset

echo -e "\n[3/3] Retrieving API Gateway URL and API Key..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

API_KEY_ID=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiKeyId'].OutputValue" \
    --output text)

API_KEY_VALUE=$(aws apigateway get-api-key \
    --api-key "${API_KEY_ID}" \
    --include-value \
    --region "${REGION}" \
    --query "value" \
    --output text)

echo "=========================================================="
echo " DEPLOYMENT SUCCESSFUL!"
echo "=========================================================="
echo "Base API Endpoint: ${API_URL}"
echo "API Key ID:        ${API_KEY_ID}"
echo "API Key Value:     ${API_KEY_VALUE}"
echo -e "\nExample cURL Commands for Testing:"
echo "----------------------------------------------------------"
echo "curl -H \"x-api-key: ${API_KEY_VALUE}\" \"${API_URL}personal\""
echo "curl -H \"x-api-key: ${API_KEY_VALUE}\" \"${API_URL}experience\""
echo "curl -H \"x-api-key: ${API_KEY_VALUE}\" \"${API_URL}education\""
echo "curl -H \"x-api-key: ${API_KEY_VALUE}\" \"${API_URL}skills\""
echo "curl \"${API_URL}health\"   # Public health check"
echo "=========================================================="
