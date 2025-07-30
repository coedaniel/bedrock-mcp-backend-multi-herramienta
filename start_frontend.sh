#!/bin/bash

# 🌐 Script de inicio para Frontend Web
echo "🌐 Iniciando Frontend Web..."

# Cambiar al directorio del frontend
cd /home/ec2-user/bedrock-mcp-backend-complete/frontend

# Verificar que existe el archivo HTML
if [ ! -f "index.html" ]; then
    echo "❌ Error: No se encuentra index.html"
    exit 1
fi

echo "📁 Sirviendo archivos desde: $(pwd)"
echo "🔗 URL Local: http://localhost:3000"
echo "🔗 URL Externa: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3000"
echo ""
echo "📋 Funcionalidades disponibles:"
echo "   🔧 Herramientas MCP"
echo "   📋 Generador SOW"
echo "   🧮 Calculadora AWS"
echo "   📁 Gestión de archivos"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo "=" * 50

# Ejecutar servidor Python simple
python3 server.py
