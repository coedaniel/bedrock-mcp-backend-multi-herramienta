# 🚀 Bedrock MCP Backend Multi-Herramienta

Backend universal para **Bedrock Function Calling + MCP + S3** que procesa dinámicamente cualquier herramienta MCP sin modificar código.

## 🎯 Características

- **🔧 Soporte dinámico** para cualquier herramienta MCP (30+ herramientas)
- **📁 Subida automática a S3** con estructura por proyectos
- **🔐 URLs presignadas** para seguridad
- **📊 Logging detallado** y auditoría completa
- **🎨 Soporte multi-formato** (PNG, SVG, CSV, XLSX, YAML, JSON, DOCX, TXT)
- **⚡ Procesamiento rápido** (1-3 segundos)

## 🏗️ Arquitectura

```
Bedrock Nova/Sonnet → Backend (puerto 8000) → MCP Server → S3 Upload → Respuesta
```

## 📁 Estructura del Proyecto

```
bedrock-mcp-backend/
├── app.py                 # Backend principal FastAPI
├── mcp_client.py          # Cliente MCP dinámico
├── s3_utils.py            # Utilidades S3 con URLs presignadas
├── config.py              # Configuración global
├── requirements.txt       # Dependencias Python
├── start.sh              # Script de inicio
└── README.md             # Documentación

mcp-s3-wrapper/           # Wrapper MCP con interceptación S3
├── app.py                # Proxy MCP con subida S3
├── requirements.txt      # Dependencias
└── README.md            # Documentación del wrapper
```

## 🚀 Instalación y Uso

### Prerrequisitos

- Python 3.9+
- AWS CLI configurado
- Permisos IAM para S3

### Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd bedrock-mcp-backend

# Instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
export AWS_REGION="us-east-1"
export S3_BUCKET="tu-bucket"
export MCP_BASE_URL="https://mcp.danielingram.shop/bedrock/tool-use"

# Iniciar backend
./start.sh
```

### Uso con Bedrock

```json
POST /bedrock/tool-use
{
  "toolUse": {
    "toolUseId": "user-request-123",
    "name": "generate_diagram",
    "input": {
      "code": "código del diagrama",
      "project_name": "mi-proyecto"
    }
  }
}
```

### Respuesta

```json
{
  "toolResult": {
    "toolUseId": "user-request-123",
    "content": [
      {"text": "✅ generate_diagram ejecutado exitosamente"},
      {"text": "📁 Archivo: diagrama.png"},
      {"text": "🔗 URL: https://bucket.s3.amazonaws.com/..."},
      {"text": "📋 Proyecto: mi-proyecto"},
      {"text": "⏱️ Tiempo: 2.18s"}
    ]
  }
}
```

## 🔧 Herramientas MCP Soportadas

- `generate_diagram` - Generación de diagramas AWS
- `search_documentation` - Búsqueda en documentación AWS
- `read_documentation` - Lectura de documentación
- `get_serverless_templates` - Templates serverless
- `list_icons` - Iconos disponibles
- **Y cualquier otra herramienta MCP** sin modificar código

## 📊 Endpoints Disponibles

- `POST /bedrock/tool-use` - Procesar tool_use de Bedrock
- `GET /health` - Health check
- `GET /` - Información del servicio
- `GET /projects/{project_name}/files` - Listar archivos por proyecto

## 🔐 Configuración de Seguridad

### Variables de Entorno

```bash
AWS_REGION=us-east-1
S3_BUCKET=tu-bucket
USE_PRESIGNED_URLS=true
PRESIGNED_URL_EXPIRATION=3600
LOG_LEVEL=INFO
```

### Permisos IAM Requeridos

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::tu-bucket/arquitecturas/*"
    }
  ]
}
```

## 📈 Monitoreo y Logs

El backend incluye logging detallado:

```
2025-07-29 02:13:22 - INFO - 🎯 Nueva solicitud Bedrock - ID: 55aca866
2025-07-29 02:13:22 - INFO - 🔧 Procesando herramienta: generate_diagram
2025-07-29 02:13:22 - INFO - 📋 Proyecto: mi-proyecto
2025-07-29 02:13:24 - INFO - ✅ MCP respondió exitosamente
2025-07-29 02:13:24 - INFO - 📤 Archivo subido: https://...
2025-07-29 02:13:24 - INFO - 🎉 Solicitud completada - Tiempo: 1.74s
```

## 🚀 Despliegue en Producción

### Docker

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  bedrock-mcp-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AWS_REGION=us-east-1
      - S3_BUCKET=tu-bucket
    volumes:
      - ~/.aws:/root/.aws:ro
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.

## 🆘 Soporte

Para soporte y preguntas:
- Crear issue en GitHub
- Revisar logs en `/app/app.log`
- Verificar configuración AWS

---

**Desarrollado para integración perfecta entre Bedrock Function Calling y MCP Servers** 🚀
