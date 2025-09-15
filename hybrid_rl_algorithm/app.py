#!/usr/bin/env python3
import http.server
import socketserver
import json
import argparse
from urllib.parse import urlparse

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/pal_logs':
            length = int(self.headers.get('Content-Length', '0'))
            data = self.rfile.read(length)
            try:
                payload = json.loads(data.decode('utf-8'))
            except Exception:
                payload = None
            # append to file in data/
            with open('data/pal_results.jsonl', 'a') as f:
                f.write(json.dumps(payload) + '\n')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        return super().do_POST()

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8000)
    args = ap.parse_args()
    with ReusableTCPServer(("", args.port), Handler) as httpd:
        print(f"Serving on http://localhost:{args.port}")
        httpd.serve_forever()


