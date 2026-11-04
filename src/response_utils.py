"""
Response Utility Module for AWS Lambda

Provides standardized HTTP responses, CORS headers, and JSON serialization
(handling Decimal types from DynamoDB).
"""

import json
from decimal import Decimal
from typing import Any, Dict, Optional


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that converts DynamoDB Decimal objects to int or float."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


def build_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Constructs an API Gateway compatible HTTP response dictionary.

    Args:
        status_code: HTTP status code (200, 400, 404, 500, etc.)
        body: Python dict, list, or primitive to be JSON serialized.
        headers: Optional custom headers to merge with default CORS headers.

    Returns:
        Dict formatted for API Gateway proxy integration.
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS,HEAD",
        "Cache-Control": "max-age=300, public"
    }

    if headers:
        default_headers.update(headers)

    payload = json.dumps(body, cls=DecimalEncoder, indent=2) if not isinstance(body, str) else body

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": payload
    }


def success_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    """Helper for successful responses."""
    return build_response(status_code=status_code, body=data)


def error_response(message: str, status_code: int = 400, error_code: Optional[str] = None) -> Dict[str, Any]:
    """Helper for error responses."""
    error_body = {
        "error": {
            "message": message,
            "statusCode": status_code
        }
    }
    if error_code:
        error_body["error"]["code"] = error_code
    return build_response(status_code=status_code, body=error_body)
