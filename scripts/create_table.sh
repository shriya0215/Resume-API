#!/usr/bin/env bash
# ==============================================================================
# Creates the Amazon DynamoDB table for Serverless Resume API via AWS CLI
# ==============================================================================

set -euo pipefail

TABLE_NAME="${1:-ServerlessResumeTable}"
REGION="${2:-us-east-1}"

echo "Creating DynamoDB table '${TABLE_NAME}' in region '${REGION}'..."

aws dynamodb create-table \
    --table-name "${TABLE_NAME}" \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region "${REGION}"

echo "Waiting for table to become ACTIVE..."
aws dynamodb wait table-exists --table-name "${TABLE_NAME}" --region "${REGION}"

echo "Table '${TABLE_NAME}' is now ACTIVE and ready."
