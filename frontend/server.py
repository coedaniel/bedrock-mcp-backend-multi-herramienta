#!/usr/bin/env python3
"""
🌐 Servidor Web Simple para Frontend
Sirve la interfaz web estática en puerto 3000
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Configuración
PORT = 3000
DIRECTORY = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Agregar headers CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Manejar preflight requests
        self.send_response(200)
        self.end_headers()

def main():
    print(f"🌐 Iniciando servidor web en puerto {PORT}")
    print(f"📁 Sirviendo archivos desde: {DIRECTORY}")
    print(f"🔗 URL: http://localhost:{PORT}")
    print(f"🔗 URL Externa: http://<IP-PUBLICA>:{PORT}")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ Servidor iniciado exitosamente")
            print("Presiona Ctrl+C para detener el servidor")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
