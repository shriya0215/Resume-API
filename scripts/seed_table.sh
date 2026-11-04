#!/usr/bin/env bash
# ==============================================================================
# Seeds the DynamoDB table using AWS CLI batch-write-item
# ==============================================================================

set -euo pipefail

TABLE_NAME="${1:-ServerlessResumeTable}"
REGION="${2:-us-east-1}"

echo "Seeding DynamoDB table '${TABLE_NAME}' in '${REGION}'..."

TEMP_FILE=$(mktemp)
sed "s/ServerlessResumeTable/${TABLE_NAME}/g" scripts/seed_dynamodb_items.json > "${TEMP_FILE}"

aws dynamodb batch-write-item --request-items "file://${TEMP_FILE}" --region "${REGION}"

rm -f "${TEMP_FILE}"

echo "Batch write completed successfully."
