"""
Unit Tests for Serverless Resume API Handler

Tests routing, response generation, error handling, CORS headers,
and JSON fallback parsing across all required endpoints.
Uses Python's built-in unittest framework (no external packages required).
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Add src directory to system path
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

import app
import response_utils


class TestResumeApi(unittest.TestCase):

    def setUp(self):
        # Ensure we test with local resume.json fallback
        if "RESUME_TABLE_NAME" in os.environ:
            del os.environ["RESUME_TABLE_NAME"]
        app._cached_resume_json = None

    def test_resume_json_file_validity(self):
        """Verifies that the resume.json file is valid and has all required root keys."""
        data = app.load_resume_from_file()
        self.assertIsInstance(data, dict)
        self.assertIn("personal", data)
        self.assertIn("experience", data)
        self.assertIn("education", data)
        self.assertIn("skills", data)

    def test_get_root_and_resume_endpoint(self):
        """Tests GET / and GET /resume returns the entire resume payload."""
        for path in ["/", "/resume"]:
            event = {
                "httpMethod": "GET",
                "path": path
            }
            res = app.lambda_handler(event, None)
            self.assertEqual(res["statusCode"], 200)
            self.assertEqual(res["headers"]["Content-Type"], "application/json")
            self.assertEqual(res["headers"]["Access-Control-Allow-Origin"], "*")

            body = json.loads(res["body"])
            self.assertIn("personal", body)
            self.assertIn("experience", body)
            self.assertIn("education", body)
            self.assertIn("skills", body)

    def test_get_personal_endpoint(self):
        """Tests GET /personal returns personal contact details and bio."""
        event = {
            "httpMethod": "GET",
            "path": "/personal"
        }
        res = app.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)

        body = json.loads(res["body"])
        self.assertIn("name", body)
        self.assertIn("email", body)
        self.assertIn("title", body)
        self.assertIn("summary", body)
        self.assertEqual(body["name"], "Alex Mercer")

    def test_get_experience_endpoint(self):
        """Tests GET /experience returns a list of job experiences."""
        event = {
            "httpMethod": "GET",
            "path": "/experience"
        }
        res = app.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)

        body = json.loads(res["body"])
        self.assertIsInstance(body, list)
        self.assertGreater(len(body), 0)
        first_job = body[0]
        self.assertIn("company", first_job)
        self.assertIn("role", first_job)
        self.assertIn("achievements", first_job)

    def test_get_education_endpoint(self):
        """Tests GET /education returns degrees and courses."""
        event = {
            "httpMethod": "GET",
            "path": "/education"
        }
        res = app.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)

        body = json.loads(res["body"])
        self.assertIsInstance(body, list)
        self.assertGreater(len(body), 0)
        edu = body[0]
        self.assertIn("institution", edu)
        self.assertIn("degree", edu)

    def test_get_skills_endpoint(self):
        """Tests GET /skills returns categorized technical proficiencies."""
        event = {
            "httpMethod": "GET",
            "path": "/skills"
        }
        res = app.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)

        body = json.loads(res["body"])
        self.assertIsInstance(body, dict)
        self.assertIn("cloudAndServerless", body)
        self.assertIn("programmingLanguages", body)
        self.assertIn("databasesAndStorage", body)
        self.assertIn("AWS Lambda", body["cloudAndServerless"])

    def test_health_check_endpoint(self):
        """Tests GET /health returns service health status."""
        event = {
            "httpMethod": "GET",
            "path": "/health"
        }
        res = app.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)

        body = json.loads(res["body"])
        self.assertEqual(body["status"], "HEALTHY")
        self.assertEqual(body["service"], "Serverless Resume API")

    def test_cors_options_preflight(self):
        """Tests that OPTIONS preflight requests return 200 with permissive CORS headers."""
        event = {
            "httpMethod": "OPTIONS",
            "path": "/personal"
        }
        res = app.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)
        self.assertIn("Access-Control-Allow-Origin", res["headers"])
        self.assertIn("Access-Control-Allow-Methods", res["headers"])
        self.assertIn("Access-Control-Allow-Headers", res["headers"])

    def test_unsupported_http_method(self):
        """Tests that non-GET requests (e.g. POST, PUT, DELETE) return 405 Method Not Allowed."""
        for method in ["POST", "PUT", "DELETE", "PATCH"]:
            event = {
                "httpMethod": method,
                "path": "/personal"
            }
            res = app.lambda_handler(event, None)
            self.assertEqual(res["statusCode"], 405)
            body = json.loads(res["body"])
            self.assertEqual(body["error"]["code"], "METHOD_NOT_ALLOWED")

    def test_not_found_endpoint(self):
        """Tests that non-existent paths return 404 Not Found."""
        event = {
            "httpMethod": "GET",
            "path": "/invalid/path"
        }
        res = app.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 404)
        body = json.loads(res["body"])
        self.assertEqual(body["error"]["code"], "NOT_FOUND")

    def test_response_utils_helpers(self):
        """Tests success and error helper functions."""
        succ = response_utils.success_response({"test": 123})
        self.assertEqual(succ["statusCode"], 200)

        err = response_utils.error_response("Bad input", 400, "BAD_REQUEST")
        self.assertEqual(err["statusCode"], 400)
        body = json.loads(err["body"])
        self.assertEqual(body["error"]["message"], "Bad input")
        self.assertEqual(body["error"]["code"], "BAD_REQUEST")


if __name__ == "__main__":
    unittest.main()
