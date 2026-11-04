"""
DynamoDB Service Layer

Handles reading and writing resume sections to/from Amazon DynamoDB.
Follows AWS Single-Table Design principles with composite Partition Key (PK)
and Sort Key (SK).
"""

import os
import logging
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Table name configured via environment variable
TABLE_NAME = os.environ.get("RESUME_TABLE_NAME", "ServerlessResumeTable")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

_dynamodb_resource = None


def get_dynamodb_resource():
    """Lazy initialize the boto3 DynamoDB resource."""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource("dynamodb", region_name=AWS_REGION)
    return _dynamodb_resource


def get_table():
    """Returns the DynamoDB Table instance."""
    return get_dynamodb_resource().Table(TABLE_NAME)


def get_section_from_db(section_name: str) -> Optional[Any]:
    """
    Fetches a specific resume section from DynamoDB.
    
    DynamoDB Key Schema:
      PK: SECTION#<section_name>
      SK: DATA
      
    Returns:
      The payload stored in the item's 'data' attribute, or None if not found.
    """
    try:
        table = get_table()
        pk = f"SECTION#{section_name.lower()}"
        sk = "DATA"
        
        response = table.get_item(
            Key={
                "PK": pk,
                "SK": sk
            }
        )
        item = response.get("Item")
        if item and "data" in item:
            return item["data"]
        return None
    except ClientError as e:
        logger.warning("ClientError retrieving section '%s' from DynamoDB: %s", section_name, e)
        return None
    except Exception as e:
        logger.warning("Unexpected error querying DynamoDB for section '%s': %s", section_name, e)
        return None


def get_full_resume_from_db() -> Optional[Dict[str, Any]]:
    """
    Retrieves the entire resume from DynamoDB.
    Tries primary 'RESUME' / 'FULL' item first, or aggregates individual sections.
    """
    try:
        table = get_table()
        # Check if full aggregated resume exists
        res = table.get_item(Key={"PK": "RESUME", "SK": "FULL"})
        if "Item" in res and "data" in res["Item"]:
            return res["Item"]["data"]

        # Otherwise aggregate standard sections
        sections = ["personal", "experience", "education", "skills", "certifications", "projects"]
        resume: Dict[str, Any] = {}
        found_any = False

        for sec in sections:
            sec_data = get_section_from_db(sec)
            if sec_data is not None:
                resume[sec] = sec_data
                found_any = True

        return resume if found_any else None
    except Exception as e:
        logger.warning("Error fetching full resume from DynamoDB: %s", e)
        return None


def put_section_to_db(section_name: str, data: Any) -> bool:
    """
    Puts/updates a specific resume section in DynamoDB.
    """
    try:
        table = get_table()
        pk = f"SECTION#{section_name.lower()}"
        sk = "DATA"
        table.put_item(
            Item={
                "PK": pk,
                "SK": sk,
                "section": section_name.lower(),
                "data": data
            }
        )
        return True
    except Exception as e:
        logger.error("Failed to put section '%s' to DynamoDB: %s", section_name, e)
        return False


def seed_resume_data(resume_dict: Dict[str, Any]) -> bool:
    """
    Seeds all sections from a resume dictionary into DynamoDB.
    Also saves a 'RESUME' / 'FULL' composite record for fast single-call retrieval.
    """
    try:
        table = get_table()
        with table.batch_writer() as batch:
            # Seed each section individually
            for section_key, section_content in resume_dict.items():
                batch.put_item(
                    Item={
                        "PK": f"SECTION#{section_key.lower()}",
                        "SK": "DATA",
                        "section": section_key.lower(),
                        "data": section_content
                    }
                )
            # Store full resume item
            batch.put_item(
                Item={
                    "PK": "RESUME",
                    "SK": "FULL",
                    "section": "all",
                    "data": resume_dict
                }
            )
        logger.info("Successfully seeded resume data into DynamoDB table '%s'", TABLE_NAME)
        return True
    except Exception as e:
        logger.error("Failed to seed resume data into DynamoDB: %s", e)
        return False
