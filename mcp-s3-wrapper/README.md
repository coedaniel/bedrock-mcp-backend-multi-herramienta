# 🔄 MCP S3 Wrapper

Proxy que intercepta herramientas MCP específicas (como generate_diagram) y agrega funcionalidad de subida automática a S3.

## 🎯 Funcionalidad

- **Proxy transparente** para herramientas MCP
- **Intercepta generate_diagram** para subir archivos a S3
- **Mantiene compatibilidad** con el MCP original
- **Logging detallado** del proceso

## 🏗️ Arquitectura

```
Backend → MCP S3 Wrapper → MCP Original
                ↓
            Intercepta archivos
                ↓
            Sube a S3
                ↓
            Modifica respuesta
```

## 📁 Archivos

- `app.py` - Proxy MCP con interceptación S3
- `requirements.txt` - Dependencias

## 🚀 Uso

```bash
# Instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar variables
export AWS_REGION="us-east-1"
export S3_BUCKET="controlwebinars2025"
export ORIGINAL_MCP_URL="https://mcp.danielingram.shop/bedrock/tool-use"

# Iniciar en puerto 8001
python app.py
```

## 🔧 Configuración del Backend

Para usar este wrapper, configurar el backend principal:

```python
# En config.py del backend
MCP_BASE_URL = "http://localhost:8001/bedrock/tool-use"
```

## ⚠️ Limitación Actual

El wrapper intenta descargar archivos del MCP original vía HTTP, pero el MCP server no expone los archivos (devuelve 404). 

**Solución recomendada**: Modificar el MCP server original para subir directamente a S3 o exponer archivos vía HTTP.

## 📊 Logs

```
🔧 Procesando herramienta: generate_diagram
📁 Interceptando archivo: diagrama.png
📥 Solicitando archivo: https://mcp.../files/path
⚠️ No se pudo descargar archivo: 404
```
