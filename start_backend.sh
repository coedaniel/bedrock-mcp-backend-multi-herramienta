#!/bin/bash

# 🚀 Script de inicio para Backend MCP
echo "🚀 Iniciando Bedrock MCP Backend..."

# Cambiar al directorio del backend
cd /home/ec2-user/bedrock-mcp-backend-complete/bedrock-mcp-backend

# Verificar dependencias
echo "📦 Verificando dependencias..."
python3 -c "
import sys
sys.path.append('.')
try:
    from document_processors import generate_sow_document, generate_aws_calculator
    from file_handler import file_handler
    from document_endpoints import router
    from s3_utils import upload_to_s3, generate_presigned_url
    print('✅ Todas las dependencias están disponibles')
except Exception as e:
    print(f'❌ Error en dependencias: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Error en verificación de dependencias"
    exit 1
fi

# Configurar variables de entorno
export AWS_REGION=${AWS_REGION:-us-east-1}
export S3_BUCKET=${S3_BUCKET:-controlwebinars2025}
export MCP_BASE_URL=${MCP_BASE_URL:-https://mcp.danielingram.shop/bedrock/tool-use}
export USE_PRESIGNED_URLS=${USE_PRESIGNED_URLS:-true}
export PRESIGNED_URL_EXPIRATION=${PRESIGNED_URL_EXPIRATION:-3600}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "⚙️ Configuración:"
echo "   AWS_REGION: $AWS_REGION"
echo "   S3_BUCKET: $S3_BUCKET"
echo "   MCP_BASE_URL: $MCP_BASE_URL"
echo "   USE_PRESIGNED_URLS: $USE_PRESIGNED_URLS"

# Crear directorio de logs si no existe
mkdir -p logs

# Iniciar servidor
echo "🌐 Iniciando servidor en puerto 8000..."
echo "🔗 URL: http://localhost:8000"
echo "📋 Health Check: http://localhost:8000/health"
echo "📚 Docs: http://localhost:8000/docs"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo "=" * 50

# Ejecutar con uvicorn
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
