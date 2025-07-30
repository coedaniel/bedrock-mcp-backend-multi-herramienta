#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
from urllib.error import HTTPError, URLError

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        # Proxy requests to backend
        if self.path.startswith('/chat') or self.path.startswith('/system-prompt'):
            self.proxy_to_backend()
        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        # Handle API requests
        if self.path.startswith('/system-prompt') or self.path.startswith('/health'):
            self.proxy_to_backend()
        # Handle static files
        elif self.path == '/' or self.path == '/index.html':
            self.path = '/index_q_style.html'
            super().do_GET()
        else:
            super().do_GET()

    def proxy_to_backend(self):
        try:
            # Read request body for POST requests
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create request to backend
            backend_url = f"http://localhost:8001{self.path}"
            
            if self.command == 'POST':
                req = urllib.request.Request(
                    backend_url,
                    data=post_data,
                    headers={'Content-Type': 'application/json'}
                )
            else:
                req = urllib.request.Request(backend_url)
            
            # Make request to backend
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read()
                
                # Send response
                self.send_response(response.getcode())
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(response_data)
                
        except HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({"detail": f"Backend error: {e.reason}"})
            self.wfile.write(error_response.encode())
            
        except URLError as e:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({"detail": f"Backend unavailable: {str(e)}"})
            self.wfile.write(error_response.encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({"detail": f"Proxy error: {str(e)}"})
            self.wfile.write(error_response.encode())

if __name__ == "__main__":
    PORT = 3005
    
    # Change to frontend directory
    os.chdir('/home/ec2-user/bedrock-chat-new/frontend')
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"🚀 Frontend Amazon Q Style server running on port {PORT}")
        print(f"📱 Access: http://localhost:{PORT}")
        print(f"🔗 Public: http://bedrock-playground.danielingram.shop")
        print(f"🎯 Backend proxy: localhost:8001")
        httpd.serve_forever()
