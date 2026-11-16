"""
Local Development Server for Serverless Resume API

Runs a lightweight HTTP server on localhost that translates HTTP requests
into API Gateway proxy events and invokes the Lambda handler.
Zero external dependencies required (uses standard library http.server).

Usage:
    python local_server.py
    Open http://localhost:8000 in your browser
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import app

PORT = 8000


class LocalApiGatewayHandler(BaseHTTPRequestHandler):
    """Bridges standard HTTP requests to the AWS Lambda handler."""

    def _dispatch(self, method: str):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}

        # Build simulated API Gateway proxy event
        headers = {k.lower(): v for k, v in self.headers.items()}
        event = {
            "httpMethod": method,
            "path": path,
            "queryStringParameters": query_params if query_params else None,
            "headers": headers,
            "requestContext": {
                "stage": "local",
                "httpMethod": method,
                "identity": {
                    "sourceIp": self.client_address[0]
                }
            }
        }

        # Invoke Lambda handler
        response = app.lambda_handler(event, None)

        status_code = response.get("statusCode", 200)
        res_headers = response.get("headers", {})
        body = response.get("body", "")

        self.send_response(status_code)
        for h_name, h_val in res_headers.items():
            self.send_header(h_name, h_val)
        self.end_headers()

        if isinstance(body, str):
            self.wfile.write(body.encode("utf-8"))
        else:
            self.wfile.write(json.dumps(body).encode("utf-8"))

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_OPTIONS(self):
        self._dispatch("OPTIONS")

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, LocalApiGatewayHandler)
    print("=" * 65)
    print(f"🚀 Serverless Resume API Local Server is running!")
    print(f"👉 Local URL: http://localhost:{PORT}")
    print("=" * 65)
    print(f"Available Endpoints:")
    print(f"  • http://localhost:{PORT}/resume       (Full Resume)")
    print(f"  • http://localhost:{PORT}/personal     (Personal Info)")
    print(f"  • http://localhost:{PORT}/experience   (Work Experience)")
    print(f"  • http://localhost:{PORT}/education    (Education)")
    print(f"  • http://localhost:{PORT}/skills       (Skills)")
    print(f"  • http://localhost:{PORT}/certifications (Certifications)")
    print(f"  • http://localhost:{PORT}/projects     (Projects)")
    print(f"  • http://localhost:{PORT}/health       (Health Check)")
    print("=" * 65)
    print("Press Ctrl+C to stop the server.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local server...")
        httpd.server_close()
        print("Server stopped.")


if __name__ == "__main__":
    run_server()
