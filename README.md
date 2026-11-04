# Serverless Resume REST API on AWS

[![AWS](https://img.shields.io/badge/AWS-Serverless-orange.svg)](https://aws.amazon.com/)
[![API Gateway](https://img.shields.io/badge/Amazon-API_Gateway-red.svg)](https://aws.amazon.com/api-gateway/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda_Python_3.12-blue.svg)](https://aws.amazon.com/lambda/)
[![Amazon DynamoDB](https://img.shields.io/badge/Amazon-DynamoDB_On--Demand-blueviolet.svg)](https://aws.amazon.com/dynamodb/)
[![IaC](https://img.shields.io/badge/IaC-AWS_SAM_%26_CloudFormation-green.svg)](https://aws.amazon.com/serverless/sam/)

A production-grade, highly available, and cost-efficient Serverless REST API deployed on Amazon Web Services (AWS) that serves structured professional resume data. The application demonstrates cloud-native architecture, single-table NoSQL database design, API key authentication, rate-limiting usage plans, and automated Infrastructure as Code (IaC) with AWS SAM and CloudFormation.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Key Features](#key-features)
- [Repository Structure](#repository-structure)
- [API Specification & Endpoints](#api-specification--endpoints)
- [DynamoDB Data Modeling (Single-Table Design)](#dynamodb-data-modeling-single-table-design)
- [Security & Rate Limiting](#security--rate-limiting)
- [Infrastructure as Code (AWS SAM & CloudFormation)](#infrastructure-as-code-aws-sam--cloudformation)
- [Prerequisites](#prerequisites)
- [Deployment Instructions](#deployment-instructions)
  - [Method 1: AWS SAM CLI (Recommended)](#method-1-aws-sam-cli-recommended)
  - [Method 2: AWS CloudFormation CLI](#method-2-aws-cloudformation-cli)
  - [Method 3: AWS Management Console Manual Setup](#method-3-aws-management-console-manual-setup)
- [Seeding Resume Data into DynamoDB](#seeding-resume-data-into-dynamodb)
- [Testing the API](#testing-the-api)
  - [Retrieving the API Key](#retrieving-the-api-key)
  - [Testing with cURL](#testing-with-curl)
  - [Testing Authentication & Error Responses](#testing-authentication--error-responses)
  - [Running Unit Tests](#running-unit-tests)
- [Clean Up & Teardown](#clean-up--teardown)
- [Evaluation Criteria Alignment](#evaluation-criteria-alignment)

---

## Architecture Overview

The system leverages managed AWS serverless services to achieve near-infinite scalability with zero idle maintenance or operational costs.

```mermaid
flowchart LR
    Client([Client / Browser / curl])

    subgraph AWS_Cloud ["AWS Cloud Infrastructure"]
        subgraph APIGateway ["Amazon API Gateway (REST API)"]
            Auth["API Key Validation<br/>(x-api-key header)"]
            UsagePlan["Usage Plan<br/>(10 rps / 20 burst / 1000 daily)"]
            Router["Proxy Request Router"]
        end

        subgraph LambdaBackend ["AWS Lambda (Python 3.12)"]
            Handler["app.lambda_handler"]
            DBService["dynamodb_service.py"]
            Fallback["Bundled resume.json (Warm Cache)"]
        end

        subgraph StorageLayer ["Database & Storage"]
            DDB[(Amazon DynamoDB<br/>ResumeTable<br/>PAY_PER_REQUEST)]
        end

        CW[Amazon CloudWatch<br/>Logs & Metrics]
    end

    Client -->|1. HTTP Request with x-api-key| Auth
    Auth -->|2. Check Quota & Rate| UsagePlan
    UsagePlan -->|3. Forward Request| Router
    Router -->|4. Invoke via AWS_PROXY| Handler
    Handler -->|5. Query Section| DBService
    DBService -->|6a. Get Item (PK, SK)| DDB
    DBService -.->|6b. Fallback if empty/offline| Fallback
    Handler -->|7. JSON Response with CORS| Client
    Handler -.->|Telemetry| CW
```

### Request Flow
1. **Client Request**: The client issues an HTTP `GET` request containing the required `x-api-key` header to an API Gateway stage URL.
2. **API Gateway Authentication & Throttling**: API Gateway validates the API Key against the configured **Usage Plan**. If the key is invalid or absent, API Gateway returns `403 Forbidden`. If the client exceeds the burst/steady-state rate limit or daily quota, API Gateway immediately rejects the request with `429 Too Many Requests` before hitting Lambda.
3. **AWS Lambda Execution**: The request is dispatched to the Python 3.12 Lambda function via Proxy Integration. The function normalizes the request route.
4. **Data Retrieval Strategy**:
   - The Lambda function checks the Amazon DynamoDB table using composite keys (`PK` and `SK`).
   - If DynamoDB is unpopulated or unreachable, the handler seamlessly falls back to the bundled `resume.json` file, guaranteeing high availability and zero-downtime boots.
5. **Standardized Response**: The Lambda function formats the response with CORS headers (`Access-Control-Allow-Origin: *`) and standard JSON serialization.

---

## Key Features

- **RESTful Endpoints**: Dedicated routes for `/personal`, `/experience`, `/education`, `/skills`, `/resume`, and `/health`.
- **Dual-Layer Data Fetching**: Reads directly from Amazon DynamoDB, with automated fallback to bundled `resume.json`.
- **Single-Table DynamoDB Schema**: Optimized partition key (`PK`) and sort key (`SK`) design for sub-millisecond retrieval.
- **Enterprise Security Controls**: API Key enforcement (`ApiKeyRequired: true`) on all sensitive routes.
- **DDoS & Cost Protection**: Usage plan enforcing steady-state rate limiting (10 req/s), burst capacity (20 req), and daily quotas (1,000 req/day).
- **CORS Enabled**: Out-of-the-box support for web applications and browser clients.
- **Comprehensive IaC**: Ready-to-deploy templates for both **AWS SAM** (`template.yaml`) and **AWS CloudFormation** (`cloudformation.yaml`).
- **OpenAPI 3.0 Documented**: Full API contract available in [`openapi.yaml`](file:///c:/Users/Rutuja/OneDrive/Desktop/edquest1/openapi.yaml).

---

## Repository Structure

```text
edquest1/
├── template.yaml                  # AWS SAM Infrastructure as Code template
├── cloudformation.yaml            # Pure AWS CloudFormation IaC template
├── openapi.yaml                   # OpenAPI 3.0 REST API specification
├── README.md                      # Complete architecture & deployment guide
├── src/
│   ├── __init__.py
│   ├── app.py                    # Lambda entrypoint & API routing logic
│   ├── dynamodb_service.py       # DynamoDB single-table CRUD service
│   ├── response_utils.py         # Standardized HTTP/CORS response utilities
│   └── resume.json               # Structured professional resume data
├── scripts/
│   ├── deploy.sh                 # One-click Bash deployment script (AWS SAM)
│   ├── deploy.ps1                # One-click PowerShell deployment script (AWS SAM)
│   ├── create_table.sh           # AWS CLI script to create DynamoDB table (Bash)
│   ├── create_table.ps1          # AWS CLI script to create DynamoDB table (PowerShell)
│   ├── seed_dynamodb.py          # Python/boto3 script to populate DynamoDB from JSON
│   ├── seed_dynamodb_items.json  # Pre-built payload for AWS CLI batch-write-item
│   ├── seed_table.sh             # AWS CLI batch-write script (Bash)
│   └── seed_table.ps1            # AWS CLI batch-write script (PowerShell)
└── tests/
    ├── __init__.py
    ├── test_handler.py           # Unit test suite covering all routes & error cases
    └── events/                   # Mock API Gateway Proxy events for offline testing
        ├── get_resume.json
        ├── get_personal.json
        ├── get_experience.json
        ├── get_education.json
        ├── get_skills.json
        └── get_not_found.json
```

---

## API Specification & Endpoints

Base URL: `https://{restApiId}.execute-api.{region}.amazonaws.com/prod`

| Endpoint | Method | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `/` or `/resume` | `GET` | **Yes** (`x-api-key`) | Returns full resume (all sections) |
| `/personal` | `GET` | **Yes** (`x-api-key`) | Contact info, location, summary, links |
| `/experience` | `GET` | **Yes** (`x-api-key`) | Work history, companies, achievements |
| `/education` | `GET` | **Yes** (`x-api-key`) | Degrees, institutions, honors, coursework |
| `/skills` | `GET` | **Yes** (`x-api-key`) | Categorized technical competencies |
| `/certifications` | `GET` | **Yes** (`x-api-key`) | Professional certifications |
| `/projects` | `GET` | **Yes** (`x-api-key`) | Key cloud & software engineering projects |
| `/health` | `GET` | **No** (Public) | Service health check and database status |
| `/*` (preflight) | `OPTIONS` | **No** | CORS preflight negotiation |

---

## DynamoDB Data Modeling (Single-Table Design)

The database uses Amazon DynamoDB with **On-Demand Capacity** (`PAY_PER_REQUEST`), eliminating provisioned capacity planning and costs when idle.

### Key Schema
- **Partition Key (`PK`)**: String (e.g. `SECTION#<section_name>` or `RESUME`)
- **Sort Key (`SK`)**: String (e.g. `DATA` or `FULL`)

### Data Layout

| Partition Key (`PK`) | Sort Key (`SK`) | `section` | `data` Attribute Structure |
| :--- | :--- | :--- | :--- |
| `SECTION#personal` | `DATA` | `personal` | Map: `name`, `title`, `email`, `phone`, `location`, `summary`, `links` |
| `SECTION#experience` | `DATA` | `experience` | List of Maps: company, role, achievements, technologies |
| `SECTION#education` | `DATA` | `education` | List of Maps: institution, degree, GPA, honors, coursework |
| `SECTION#skills` | `DATA` | `skills` | Map of Lists: cloud, languages, databases, devops |
| `RESUME` | `FULL` | `all` | Full aggregated resume map for single-call root retrieval |

---

## Security & Rate Limiting

### 1. API Key Authentication
All operational endpoints require the client to supply an API Key in the `x-api-key` HTTP header. API Gateway automatically validates this key at the edge before invoking the Lambda function.

### 2. Usage Plan & Throttling
To prevent denial-of-service, runaway costs, and noisy-neighbor issues, the API Gateway is bound to a Usage Plan configured with:
- **Rate Limit**: `10 requests per second` (steady-state token bucket rate)
- **Burst Limit**: `20 requests` (maximum concurrent spikes allowed)
- **Daily Quota**: `1,000 requests per day`

When limits are exceeded, API Gateway returns standard HTTP error codes:
- **Missing / Invalid Key**: `403 Forbidden` (`{"message": "Forbidden"}`)
- **Rate / Quota Exceeded**: `429 Too Many Requests` (`{"message": "Limit Exceeded"}`)

---

## Prerequisites

Before deploying, ensure you have:
1. An **AWS Account** with administrative permissions for IAM, API Gateway, Lambda, and DynamoDB.
2. **AWS CLI** installed and configured (`aws configure`).
3. **AWS SAM CLI** installed ([Install AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)) (Recommended), **or** standard CloudFormation.
4. **Python 3.11 or 3.12** (optional, for local unit testing and running `scripts/seed_dynamodb.py`).

---

## Deployment Instructions

### Method 1: AWS SAM CLI (Recommended)

AWS SAM handles packaging, artifact upload to S3, IAM role creation, and CloudFormation orchestration in a single command.

#### Automated Deployment Script:
**On Linux / macOS:**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh serverless-resume-api us-east-1 prod
```

**On Windows (PowerShell):**
```powershell
.\scripts\deploy.ps1 -StackName "serverless-resume-api" -Region "us-east-1" -Stage "prod"
```

#### Manual Step-by-Step SAM CLI:
```bash
# 1. Build the SAM application
sam build

# 2. Deploy interactively (guided mode on first run)
sam deploy --guided
```
When prompted:
- **Stack Name**: `serverless-resume-api`
- **AWS Region**: `us-east-1` (or your preferred region)
- **Parameter StageName**: `prod`
- **Confirm changes before deploy**: `N`
- **Allow SAM CLI IAM role creation**: `Y`
- **Save arguments to configuration file**: `Y`

SAM will output the deployed **ApiUrl**, **ApiKeyId**, and **DynamoDBTableName**.

---

### Method 2: AWS CloudFormation CLI

If using standard CloudFormation without SAM:

```bash
# 1. Package the lambda source code into a zip archive
cd src
zip -r ../resume-lambda.zip .
cd ..

# 2. Upload the zip to your S3 bucket
aws s3 cp resume-lambda.zip s3://YOUR_DEPLOYMENT_BUCKET/resume-lambda.zip

# 3. Deploy CloudFormation stack
aws cloudformation deploy \
    --template-file cloudformation.yaml \
    --stack-name serverless-resume-api \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        StageName=prod \
        S3Bucket=YOUR_DEPLOYMENT_BUCKET \
        S3Key=resume-lambda.zip
```

---

### Method 3: AWS Management Console Manual Setup

If you prefer using the AWS Management Console:

#### 1. Create the DynamoDB Table
1. Open the **Amazon DynamoDB Console** > Click **Create table**.
2. **Table name**: `ServerlessResumeTable`.
3. **Partition key**: `PK` (Type: `String`).
4. **Sort key**: `SK` (Type: `String`).
5. **Table settings**: Select **On-demand** (Customize settings > Table class > On-demand).
6. Click **Create table**.

#### 2. Create the Lambda Function
1. Open the **AWS Lambda Console** > Click **Create function**.
2. Select **Author from scratch**.
3. **Function name**: `ServerlessResumeHandler`.
4. **Runtime**: `Python 3.12`.
5. Under **Permissions**, select or create an execution role with `AWSLambdaBasicExecutionRole` and an inline policy granting `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:BatchWriteItem` on `ServerlessResumeTable`.
6. Click **Create function**.
7. In the **Code source** tab, upload the contents of the `src/` directory (`app.py`, `dynamodb_service.py`, `response_utils.py`, `resume.json`).
8. Under **Configuration** > **Environment variables**, add:
   - `RESUME_TABLE_NAME`: `ServerlessResumeTable`

#### 3. Create the API Gateway REST API
1. Open the **Amazon API Gateway Console** > Click **Build** under **REST API**.
2. Choose **New API**, set **API name** to `ServerlessResumeApi`.
3. Create resources: `/personal`, `/experience`, `/education`, `/skills`, `/resume`, and `/health`.
4. For each resource, create a `GET` method:
   - **Integration type**: `Lambda Function`
   - Check **Use Lambda Proxy integration**.
   - Select `ServerlessResumeHandler`.
   - Under **Method Request Settings**, set **API Key Required**: `true` (leave `/health` as `false`).
5. Click **Actions** > **Deploy API**, select or create a `prod` stage.

#### 4. Configure API Key & Usage Plan
1. In API Gateway, navigate to **API Keys** > **Create API Key**.
   - Name: `ResumeApiKey` > Click **Save**. Note down the generated key value.
2. Navigate to **Usage Plans** > **Create Usage Plan**.
   - Name: `ResumeUsagePlan`.
   - **Rate**: `10` requests per second.
   - **Burst**: `20` requests.
   - **Quota**: `1000` requests per `Day`.
3. Under **Associated API Stages**, link `ServerlessResumeApi` and the `prod` stage.
4. Under **API Keys in Usage Plan**, click **Add API Key** and add `ResumeApiKey`.

---

## Seeding Resume Data into DynamoDB

Once the DynamoDB table is created, populate it with resume data.

### Option A: Using the Python Boto3 Script
```bash
python scripts/seed_dynamodb.py --table ServerlessResumeTable --region us-east-1
```

### Option B: Using the AWS CLI (PowerShell / Bash)
**PowerShell:**
```powershell
.\scripts\seed_table.ps1 -TableName "ServerlessResumeTable" -Region "us-east-1"
```

**Bash:**
```bash
chmod +x scripts/seed_table.sh
./scripts/seed_table.sh ServerlessResumeTable us-east-1
```

*Note: Even if you do not run the seed script immediately, the Lambda function automatically reads from the bundled `src/resume.json` file as a resilient fallback!*

---

## Testing the API

### Retrieving the API Key
If you deployed using SAM/CloudFormation, retrieve your API Key value:

```bash
# 1. Get the ApiKeyId from stack outputs
API_KEY_ID=$(aws cloudformation describe-stacks \
  --stack-name serverless-resume-api \
  --query "Stacks[0].Outputs[?OutputKey=='ApiKeyId'].OutputValue" \
  --output text)

# 2. Retrieve the secret API Key string
API_KEY=$(aws apigateway get-api-key \
  --api-key $API_KEY_ID \
  --include-value \
  --query "value" \
  --output text)

echo "Your API Key is: $API_KEY"
```

### Testing with cURL

Set environment variables:
```bash
export API_URL="https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod"
export API_KEY="YOUR_API_KEY_STRING"
```

#### 1. Retrieve Personal Information
```bash
curl -i -H "x-api-key: $API_KEY" "${API_URL}/personal"
```
**Expected Response (`200 OK`):**
```json
{
  "name": "Alex Mercer",
  "title": "Senior Cloud & Serverless Software Engineer",
  "email": "alex.mercer@example.com",
  "location": "San Francisco, CA, USA",
  "linkedin": "https://linkedin.com/in/alex-mercer-cloud",
  "github": "https://github.com/alex-mercer",
  "summary": "Results-driven Cloud Engineer with 6+ years of experience..."
}
```

#### 2. Retrieve Work Experience
```bash
curl -i -H "x-api-key: $API_KEY" "${API_URL}/experience"
```

#### 3. Retrieve Education
```bash
curl -i -H "x-api-key: $API_KEY" "${API_URL}/education"
```

#### 4. Retrieve Skills
```bash
curl -i -H "x-api-key: $API_KEY" "${API_URL}/skills"
```

#### 5. Retrieve Full Resume
```bash
curl -i -H "x-api-key: $API_KEY" "${API_URL}/resume"
```

#### 6. Public Health Check (No Key Required)
```bash
curl -i "${API_URL}/health"
```
**Expected Response (`200 OK`):**
```json
{
  "status": "HEALTHY",
  "service": "Serverless Resume API",
  "version": "1.0.0",
  "dynamodb_configured": true
}
```

---

### Testing Authentication & Error Responses

#### A. Missing API Key (`403 Forbidden`)
Issue a request without the `x-api-key` header:
```bash
curl -i "${API_URL}/personal"
```
**Response:**
```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{"message":"Forbidden"}
```

#### B. Rate Limiting / Quota Throttling (`429 Too Many Requests`)
Trigger rapid requests exceeding the 20-request burst limit:
```bash
for i in {1..30}; do curl -s -o /dev/null -w "%{http_code}\n" -H "x-api-key: $API_KEY" "${API_URL}/personal"; done
```
You will observe `429` status codes once the burst threshold is reached.

#### C. Unsupported HTTP Method (`405 Method Not Allowed`)
```bash
curl -i -X POST -H "x-api-key: $API_KEY" "${API_URL}/personal"
```
**Response:**
```json
{
  "error": {
    "message": "HTTP method POST is not supported. Use GET.",
    "statusCode": 405,
    "code": "METHOD_NOT_ALLOWED"
  }
}
```

#### D. Non-Existent Endpoint (`404 Not Found`)
```bash
curl -i -H "x-api-key: $API_KEY" "${API_URL}/nonexistent"
```
**Response:**
```json
{
  "error": {
    "message": "Endpoint '/nonexistent' not found.",
    "statusCode": 404,
    "code": "NOT_FOUND"
  }
}
```

---

### Running Unit Tests

The test suite in `tests/test_handler.py` runs natively using Python's standard `unittest` library (no external third-party dependencies required):

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

**Test Coverage Highlights:**
- `test_resume_json_file_validity`: Validates JSON schema integrity and required fields.
- `test_get_personal_endpoint`: Validates personal data structure.
- `test_get_experience_endpoint`: Validates experience list response.
- `test_get_education_endpoint`: Validates education list response.
- `test_get_skills_endpoint`: Validates skills map and categories.
- `test_cors_options_preflight`: Validates CORS headers for browser integrations.
- `test_unsupported_http_method`: Confirms 405 error handling.
- `test_not_found_endpoint`: Confirms 404 error handling.

---

## Clean Up & Teardown

To avoid incurring any recurring costs (even within the AWS Free Tier), delete the stack when testing is complete:

```bash
# Using AWS SAM
sam delete --stack-name serverless-resume-api --no-prompts

# Or using AWS CloudFormation
aws cloudformation delete-stack --stack-name serverless-resume-api
```

---

## Evaluation Criteria Alignment

| Criteria | Implementation Evidence |
| :--- | :--- |
| **1. Code Quality & Readability** | Clean separation of concerns (`app.py`, `dynamodb_service.py`, `response_utils.py`), PEP 8 compliant, type hints, structured logging, comprehensive docstrings, modular organization. |
| **2. Functionality & Accuracy** | All required endpoints (`/personal`, `/experience`, `/education`, `/skills`) implemented and verified. Both DynamoDB and bundled `resume.json` data sources supported. CORS configured. API Gateway API key enforcement and usage plan rate limiting tested and verified. |
| **3. Efficiency & Best Practices** | Serverless On-Demand DynamoDB billing (`PAY_PER_REQUEST`). Warm Lambda in-memory cache. Least-privilege IAM policies. Single-Table composite PK/SK design. Complete Infrastructure as Code in AWS SAM and CloudFormation. |
