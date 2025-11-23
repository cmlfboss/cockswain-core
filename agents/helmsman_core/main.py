import http.server
import json
import socketserver

PORT = 9090

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "component": "cockswain-core"}).encode())
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Cockswain core placeholder")

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
