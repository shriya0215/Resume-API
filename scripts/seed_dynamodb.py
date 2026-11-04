#!/usr/bin/env python3
"""
Seed Resume Data into Amazon DynamoDB

Reads resume data from src/resume.json and populates the specified DynamoDB table.
Supports single-table schema with composite Partition Key (PK) and Sort Key (SK).

Usage:
    python scripts/seed_dynamodb.py --table ServerlessResumeTable --region us-east-1
"""

import argparse
import json
import os
import sys
from pathlib import Path
from decimal import Decimal

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("Error: 'boto3' is required. Run 'pip install boto3' to install.")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Seed resume data into DynamoDB")
    parser.add_argument(
        "--table",
        default=os.environ.get("RESUME_TABLE_NAME", "ServerlessResumeTable"),
        help="Name of the target DynamoDB table"
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_REGION", "us-east-1"),
        help="AWS region"
    )
    parser.add_argument(
        "--file",
        default=str(Path(__file__).parent.parent / "src" / "resume.json"),
        help="Path to resume.json file"
    )
    return parser.parse_args()


def load_json(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        # Load with Decimal parsing for float values to satisfy DynamoDB
        return json.load(f, parse_float=Decimal)


def seed_data(table_name: str, region: str, file_path: str):
    print(f"Loading resume data from: {file_path}")
    resume_data = load_json(file_path)

    print(f"Connecting to DynamoDB table '{table_name}' in region '{region}'...")
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    items_to_write = []

    # 1. Individual section items
    for section_name, section_content in resume_data.items():
        items_to_write.append({
            "PK": f"SECTION#{section_name.lower()}",
            "SK": "DATA",
            "section": section_name.lower(),
            "data": section_content
        })

    # 2. Aggregated full resume item
    items_to_write.append({
        "PK": "RESUME",
        "SK": "FULL",
        "section": "all",
        "data": resume_data
    })

    print(f"Writing {len(items_to_write)} items to DynamoDB...")

    try:
        with table.batch_writer() as batch:
            for item in items_to_write:
                batch.put_item(Item=item)
                print(f"  [+] Seeded item: PK='{item['PK']}', SK='{item['SK']}'")
        print(f"\nSuccessfully seeded all resume records into '{table_name}'!")
    except ClientError as e:
        print(f"\nAWS ClientError while seeding data: {e.response['Error']['Message']}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error while seeding data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    seed_data(table_name=args.table, region=args.region, file_path=args.file)
