"""
AWS Lambda Handler for Serverless Resume REST API

Serves resume data (personal, experience, education, skills, projects, certifications)
using Amazon API Gateway routing, reading from DynamoDB with fallback to bundled JSON.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from response_utils import error_response, success_response, build_response
import dynamodb_service

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Path to the bundled resume JSON file
JSON_FILE_PATH = Path(__file__).parent / "resume.json"

# In-memory cache for bundled resume JSON
_cached_resume_json: Optional[Dict[str, Any]] = None


def load_resume_from_file() -> Dict[str, Any]:
    """
    Reads resume data from the local JSON file.
    Implements file caching for warm Lambda invocations.
    """
    global _cached_resume_json
    if _cached_resume_json is None:
        try:
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
                _cached_resume_json = json.load(f)
            logger.info("Successfully loaded resume data from %s", JSON_FILE_PATH)
        except Exception as e:
            logger.error("Failed to read resume.json: %s", e)
            raise RuntimeError(f"Unable to load resume data file: {str(e)}")
    return _cached_resume_json


def get_data(section: Optional[str] = None, force_json: bool = False) -> Any:
    """
    Fetches resume data. Attempts DynamoDB first, falls back to local JSON file.
    If section is specified, returns only that section.
    """
    data = None

    if not force_json and os.environ.get("RESUME_TABLE_NAME"):
        try:
            if section:
                data = dynamodb_service.get_section_from_db(section)
            else:
                data = dynamodb_service.get_full_resume_from_db()
        except Exception as e:
            logger.warning("DynamoDB retrieval failed, falling back to JSON file: %s", e)

    # Fallback to local resume.json if DynamoDB was not available or empty
    if data is None:
        json_resume = load_resume_from_file()
        if section:
            data = json_resume.get(section)
        else:
            data = json_resume

    return data


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main AWS Lambda entry point for API Gateway Proxy Integration.
    Routes requests based on HTTP method and path.
    """
    logger.info("Incoming Event: %s", json.dumps(event.get("pathParameters") or event.get("rawPath") or event.get("path")))

    http_method = event.get("httpMethod", "").upper()
    # Support both API Gateway REST API (path) and HTTP API (rawPath)
    path = event.get("path") or event.get("rawPath", "/")
    query_params = event.get("queryStringParameters") or {}
    force_json = query_params.get("source", "").lower() == "json"

    # Handle CORS preflight requests
    if http_method == "OPTIONS":
        return build_response(
            status_code=200,
            body={"message": "CORS preflight successful"},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,OPTIONS,HEAD",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
            }
        )

    # Only GET requests are supported for this read-only API
    if http_method not in ["GET", "HEAD"]:
        return error_response(
            message=f"HTTP method {http_method} is not supported. Use GET.",
            status_code=405,
            error_code="METHOD_NOT_ALLOWED"
        )

    # Normalize path (strip trailing slashes, keep lowercase)
    normalized_path = path.rstrip("/").lower()
    if not normalized_path:
        normalized_path = "/"

    try:
        # Route dispatch
        if normalized_path in ["/", "/resume"]:
            resume_data = get_data(section=None, force_json=force_json)
            if resume_data:
                return success_response(resume_data)
            return error_response("Resume data not found.", status_code=404)

        elif normalized_path == "/personal":
            personal = get_data(section="personal", force_json=force_json)
            if personal:
                return success_response(personal)
            return error_response("Personal information section not found.", status_code=404)

        elif normalized_path == "/experience":
            experience = get_data(section="experience", force_json=force_json)
            if experience is not None:
                return success_response(experience)
            return error_response("Experience section not found.", status_code=404)

        elif normalized_path == "/education":
            education = get_data(section="education", force_json=force_json)
            if education is not None:
                return success_response(education)
            return error_response("Education section not found.", status_code=404)

        elif normalized_path == "/skills":
            skills = get_data(section="skills", force_json=force_json)
            if skills is not None:
                return success_response(skills)
            return error_response("Skills section not found.", status_code=404)

        elif normalized_path == "/certifications":
            certifications = get_data(section="certifications", force_json=force_json)
            if certifications is not None:
                return success_response(certifications)
            return error_response("Certifications section not found.", status_code=404)

        elif normalized_path == "/projects":
            projects = get_data(section="projects", force_json=force_json)
            if projects is not None:
                return success_response(projects)
            return error_response("Projects section not found.", status_code=404)

        elif normalized_path == "/health":
            return success_response({
                "status": "HEALTHY",
                "service": "Serverless Resume API",
                "version": "1.0.0",
                "dynamodb_configured": bool(os.environ.get("RESUME_TABLE_NAME"))
            })

        else:
            return error_response(
                message=f"Endpoint '{path}' not found.",
                status_code=404,
                error_code="NOT_FOUND"
            )

    except Exception as exc:
        logger.exception("Internal unhandled error processing request: %s", exc)
        return error_response(
            message="An internal server error occurred while processing your request.",
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR"
        )
