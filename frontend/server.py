#!/usr/bin/env python3
"""
Servidor web para Bedrock Playground Frontend
"""

import http.server
import socketserver
import os
import json
from urllib.parse import urlparse, parse_qs
import requests

PORT = 3003
BACKEND_URL = "http://localhost:8001"

class PlaygroundHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/home/ec2-user/bedrock-chat-new/frontend", **kwargs)
    
    def end_headers(self):
        # Headers de seguridad y CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        """Proxy requests to backend"""
        if self.path == '/chat':
            try:
                # Leer el cuerpo de la petición
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Reenviar al backend
                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    data=post_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=60
                )
                
                # Enviar respuesta
                self.send_response(response.status_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(response.content)
                
            except Exception as e:
                print(f"Error proxying request: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({"detail": str(e)})
                self.wfile.write(error_response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path in ['/health', '/models']:
            try:
                # Proxy to backend
                response = requests.get(f"{BACKEND_URL}{self.path}", timeout=10)
                
                self.send_response(response.status_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(response.content)
                
            except Exception as e:
                print(f"Error proxying GET request: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({"detail": str(e)})
                self.wfile.write(error_response.encode())
        else:
            # Servir archivos estáticos
            super().do_GET()

def main():
    print("🌐 Iniciando Bedrock Playground Frontend")
    print(f"📁 Sirviendo archivos desde: {os.getcwd()}")
    print(f"🔗 URL: http://localhost:{PORT}")
    print(f"🔗 Backend: {BACKEND_URL}")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), PlaygroundHandler) as httpd:
            print("✅ Servidor iniciado exitosamente")
            print("Presiona Ctrl+C para detener el servidor")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")

if __name__ == "__main__":
    main()
