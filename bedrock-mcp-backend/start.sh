#!/bin/bash

# start.sh - Script de inicio del Bedrock MCP Backend

echo "🚀 Iniciando Bedrock MCP Backend..."

# Configurar variables de entorno
export AWS_REGION="us-east-1"
export S3_BUCKET="controlwebinars2025"
export MCP_BASE_URL="https://mcp.danielingram.shop/bedrock/tool-use"
export USE_PRESIGNED_URLS="true"
export PRESIGNED_URL_EXPIRATION="3600"
export LOG_LEVEL="INFO"

# Crear directorio de logs si no existe
mkdir -p logs

# Instalar dependencias si no están instaladas
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

echo "📦 Activando entorno virtual..."
source venv/bin/activate

echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo "🔧 Configuración:"
echo "  - AWS Region: $AWS_REGION"
echo "  - S3 Bucket: $S3_BUCKET"
echo "  - MCP URL: $MCP_BASE_URL"
echo "  - URLs Presignadas: $USE_PRESIGNED_URLS"
echo "  - Log Level: $LOG_LEVEL"

echo "🚀 Iniciando servidor en puerto 8000..."
python app.py
