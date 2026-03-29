import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

os.environ.setdefault("TABLE_NAME", "aalumvej26-prod")
os.environ.setdefault("AWS_PROFILE", "graveyard-master")
os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-1")

from handler import lambda_handler

PORT = int(os.environ.get("PORT", "4000"))


class RpcHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != "/rpc":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()

        event = {"body": body}
        result = lambda_handler(event, None)

        self.send_response(result["statusCode"])
        self._cors_headers()
        for k, v in result.get("headers", {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(result["body"].encode())

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), RpcHandler)
    print(f"Backend running on http://localhost:{PORT}")
    server.serve_forever()
