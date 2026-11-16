"""
Local Development Server for Serverless Resume API with Interactive UI Dashboard

Runs a lightweight HTTP server on localhost that serves:
  1. An interactive web UI dashboard at http://localhost:8000
  2. The REST API endpoints (/personal, /experience, /education, /skills, /resume, /health)

Usage:
    python local_server.py
    (Or double-click Start_Resume_API.bat)
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add src to Python path
SRC_DIR = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, SRC_DIR)
import app

PORT = 8000
UI_FILE_PATH = os.path.join(SRC_DIR, "ui.html")


class LocalApiGatewayHandler(BaseHTTPRequestHandler):
    """Bridges standard HTTP requests to the AWS Lambda handler or Web UI."""

    def _serve_ui(self):
        try:
            with open(UI_FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error loading UI: {e}".encode("utf-8"))

    def _dispatch(self, method: str):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}
        accept_header = self.headers.get("Accept", "")

        # Serve the web UI when accessing root or /ui in a browser
        if method == "GET" and (path in ["/", "/ui"] and "text/html" in accept_header):
            self._serve_ui()
            return

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
    print(f"🚀 Serverless Resume API & UI Dashboard is running!")
    print(f"👉 Open in browser: http://localhost:{PORT}")
    print("=" * 65)
    print(f"Available Endpoints & UI:")
    print(f"  • http://localhost:{PORT}/             (Interactive Dashboard UI)")
    print(f"  • http://localhost:{PORT}/resume       (Full Resume JSON)")
    print(f"  • http://localhost:{PORT}/personal     (Personal Info JSON)")
    print(f"  • http://localhost:{PORT}/experience   (Work Experience JSON)")
    print(f"  • http://localhost:{PORT}/education    (Education JSON)")
    print(f"  • http://localhost:{PORT}/skills       (Skills JSON)")
    print(f"  • http://localhost:{PORT}/health       (Health Check JSON)")
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
