import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
import json
from core import generate_image


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._json(400, {"error": "Invalid request"})
            return

        image_base64 = body.get("image_base64")
        raw_occupation = body.get("occupation", "professional")

        if not image_base64:
            self._json(400, {"error": "No image provided"})
            return

        try:
            image_url, _ = generate_image(image_base64, raw_occupation)
            self._json(200, {"image_url": image_url})
        except ValueError:
            self._json(400, {"error": "blocked"})
        except Exception as e:
            print(f"fal.ai error: {e}")
            self._json(500, {"error": str(e)})

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass
