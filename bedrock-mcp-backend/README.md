# 🔧 Bedrock MCP Backend

Backend principal que procesa tool_use de Bedrock y los convierte en llamadas MCP dinámicas.

## 🎯 Funcionalidad

- **Recibe tool_use** de Bedrock Function Calling
- **Procesa cualquier herramienta MCP** dinámicamente
- **Sube archivos a S3** con URLs presignadas
- **Logging detallado** para auditoría
- **Organización por proyectos** automática

## 📁 Archivos

- `app.py` - Backend principal FastAPI
- `mcp_client.py` - Cliente MCP con logging
- `s3_utils.py` - Utilidades S3 y URLs presignadas
- `config.py` - Configuración global
- `start.sh` - Script de inicio

## 🚀 Uso

```bash
# Instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar variables
export AWS_REGION="us-east-1"
export S3_BUCKET="controlwebinars2025"
export MCP_BASE_URL="https://mcp.danielingram.shop/bedrock/tool-use"

# Iniciar
./start.sh
```

## 📊 Endpoints

- `POST /bedrock/tool-use` - Procesar tool_use
- `GET /health` - Health check
- `GET /` - Info del servicio
- `GET /projects/{name}/files` - Listar archivos

## 🔧 Herramientas Soportadas

Cualquier herramienta MCP:
- `generate_diagram`
- `search_documentation`
- `read_documentation`
- `get_serverless_templates`
- `list_icons`
- Y muchas más...

## 📈 Logs

```
🎯 Nueva solicitud Bedrock - ID: abc123
🔧 Procesando herramienta: generate_diagram
📋 Proyecto: mi-proyecto
✅ MCP respondió exitosamente
📤 Archivo subido: https://s3.url
🎉 Solicitud completada - Tiempo: 2.18s
```
