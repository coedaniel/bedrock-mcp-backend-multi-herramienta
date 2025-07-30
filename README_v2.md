# 🚀 Bedrock MCP Backend Multi-Herramienta v2.0

Backend completo para **Bedrock Function Calling + MCP + S3** con soporte avanzado para generación de documentos DOCX/XLSX y frontend web interactivo.

## ✨ Nuevas Funcionalidades v2.0

### 🔧 File Handler Avanzado
- **Detección automática** de archivos generados por MCP
- **Múltiples formatos**: PNG, SVG, DOCX, XLSX, PDF, TXT, CSV
- **Subida automática** a S3 con URLs presignadas
- **Organización inteligente** por proyecto y herramienta

### 📄 Generación de Documentos
- **📋 SOW Generator**: Documentos profesionales en DOCX
- **🧮 AWS Calculator**: Hojas de cálculo interactivas en XLSX
- **🎨 Templates personalizables** para diferentes tipos de proyecto
- **💰 Estimaciones de costos** con precios actualizados

### 🌐 Frontend Web Interactivo
- **Interface moderna** para interacción directa
- **4 secciones principales**: MCP Tools, SOW, Calculator, Files
- **Descarga directa** de archivos generados
- **Responsive design** para móviles y desktop

## 🏗️ Arquitectura v2.0

```
Usuario → Frontend Web (puerto 3000) → Backend API (puerto 8000) → MCP Server → S3 Storage
    ↓
Visualización → Descarga → Documentos Finales (PNG, DOCX, XLSX, SOW)
```

## 📁 Estructura del Proyecto v2.0

```
bedrock-mcp-backend-complete/
├── 📄 README_v2.md                 # Esta documentación
├── 📄 GUIA_CALCULADORA_AWS.md      # Guía paso a paso
├── 🚀 start_backend.sh             # Script inicio backend
├── 🚀 start_frontend.sh            # Script inicio frontend
│
├── 🔧 bedrock-mcp-backend/         # Backend principal
│   ├── 🐍 app.py                   # FastAPI con File Handler
│   ├── 🐍 file_handler.py          # Procesador avanzado de archivos
│   ├── 🐍 document_processors.py   # Generadores DOCX/XLSX
│   ├── 🐍 document_endpoints.py    # Endpoints para documentos
│   ├── 🐍 mcp_client.py            # Cliente MCP
│   ├── 🐍 s3_utils.py              # Utilidades S3 mejoradas
│   ├── ⚙️ config.py                # Configuración extendida
│   └── 📋 requirements.txt         # Dependencias actualizadas
│
└── 🌐 frontend/                    # Frontend web
    ├── 🌐 index.html               # Interface principal
    ├── 🐍 server.py                # Servidor web simple
    └── 📋 Funcionalidades completas
```

## 🚀 Inicio Rápido v2.0

### 1️⃣ Iniciar Backend (Terminal 1)
```bash
cd /home/ec2-user/bedrock-mcp-backend-complete
./start_backend.sh
```

### 2️⃣ Iniciar Frontend (Terminal 2)
```bash
cd /home/ec2-user/bedrock-mcp-backend-complete
./start_frontend.sh
```

### 3️⃣ Acceder a la Interface
- **Frontend Web**: http://localhost:3000
- **API Backend**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

## 🎯 Casos de Uso Principales

### 📋 Generar SOW Profesional
1. Ir a pestaña **"📋 Generar SOW"**
2. Completar información del proyecto
3. Definir objetivos y alcances
4. Generar documento DOCX profesional
5. Descargar y personalizar

### 🧮 Crear Calculadora AWS
1. Ir a pestaña **"🧮 Calculadora AWS"**
2. Especificar requerimientos técnicos
3. Configurar servicios AWS necesarios
4. Generar hoja de cálculo XLSX
5. Usar para estimaciones y propuestas

### 🔧 Ejecutar Herramientas MCP
1. Ir a pestaña **"🔧 Herramientas MCP"**
2. Seleccionar herramienta disponible
3. Configurar parámetros JSON
4. Ejecutar y obtener resultados
5. Descargar archivos generados automáticamente

### 📁 Gestionar Archivos
1. Ir a pestaña **"📁 Archivos"**
2. Buscar por proyecto
3. Ver historial de archivos generados
4. Descargar archivos anteriores

## 🔧 Endpoints API v2.0

### Endpoints Principales
- `POST /bedrock/tool-use` - Ejecutar herramientas MCP
- `POST /documents/sow/generate` - Generar SOW
- `POST /documents/calculator/generate` - Generar calculadora
- `GET /projects/{project}/files` - Listar archivos
- `GET /health` - Estado del sistema

### Endpoints de Ayuda
- `GET /documents/sow/template` - Template SOW
- `GET /documents/calculator/template` - Template calculadora
- `GET /docs` - Documentación Swagger

## 📊 Formatos Soportados v2.0

### Archivos de Entrada (MCP)
- **Imágenes**: PNG, JPG, SVG, GIF
- **Documentos**: PDF, TXT, MD
- **Datos**: JSON, CSV, YAML, XML

### Archivos de Salida (Generados)
- **📋 Documentos**: DOCX (SOW, reportes)
- **🧮 Hojas de cálculo**: XLSX (calculadoras)
- **🎨 Diagramas**: PNG, SVG (arquitecturas)
- **📄 Texto**: TXT, MD, JSON

## ⚙️ Configuración Avanzada

### Variables de Entorno
```bash
# Backend Principal
AWS_REGION=us-east-1
S3_BUCKET=controlwebinars2025
MCP_BASE_URL=https://mcp.danielingram.shop/bedrock/tool-use
USE_PRESIGNED_URLS=true
PRESIGNED_URL_EXPIRATION=3600
LOG_LEVEL=INFO

# Frontend
BACKEND_URL=http://localhost:8000
```

### Personalización de Documentos
```python
# Personalizar SOW
sow_data = {
    "project_name": "Mi Proyecto",
    "client_name": "Cliente ABC",
    "objective": "Migrar a AWS Cloud",
    "custom_sections": {
        "security": "Implementar WAF y Shield",
        "compliance": "Cumplir SOC2 y PCI-DSS"
    }
}

# Personalizar Calculadora
calc_data = {
    "project_name": "Calculadora Custom",
    "region": "us-east-1",
    "custom_services": {
        "ElastiCache": {"price": 0.017, "quantity": 2}
    }
}
```

## 🔍 Monitoreo y Logs

### Logs del Sistema
```bash
# Ver logs en tiempo real
tail -f bedrock-mcp-backend/app.log

# Filtrar por tipo
grep "SOW" bedrock-mcp-backend/app.log
grep "Calculadora" bedrock-mcp-backend/app.log
grep "File Handler" bedrock-mcp-backend/app.log
```

### Métricas Disponibles
- ⏱️ Tiempo de procesamiento por herramienta
- 📁 Archivos generados por proyecto
- 💾 Tamaño de archivos subidos
- 🔗 URLs presignadas generadas
- ❌ Errores y reintentos

## 🛠️ Desarrollo y Extensión

### Agregar Nueva Herramienta MCP
1. La herramienta se detecta automáticamente
2. File Handler procesa archivos generados
3. S3 Utils maneja la subida
4. Frontend muestra resultados

### Crear Nuevo Tipo de Documento
```python
# En document_processors.py
class CustomDocumentGenerator(DocumentProcessor):
    def generate_document(self, data):
        # Lógica de generación
        return document_bytes

# En document_endpoints.py
@router.post("/custom/generate")
async def generate_custom(request: CustomRequest):
    # Endpoint para nuevo documento
    pass
```

### Personalizar Frontend
```javascript
// Agregar nueva pestaña en index.html
function showCustomTab() {
    // Lógica de nueva funcionalidad
}
```

## 📚 Documentación Adicional

- **📋 GUIA_CALCULADORA_AWS.md** - Guía completa de calculadora
- **🏗️ ARCHITECTURE.md** - Arquitectura detallada
- **🚀 DEPLOYMENT.md** - Guía de despliegue
- **📄 LICENSE** - Licencia MIT

## 🎉 Funcionalidades Destacadas v2.0

### ✅ Completamente Implementado
- ✅ File Handler avanzado con detección automática
- ✅ Generación SOW profesional en DOCX
- ✅ Calculadora AWS interactiva en XLSX
- ✅ Frontend web completo y funcional
- ✅ Subida automática a S3 con URLs presignadas
- ✅ Soporte multi-formato (PNG, DOCX, XLSX, etc.)
- ✅ Organización por proyectos
- ✅ Logging detallado y auditoría
- ✅ Scripts de inicio automatizados
- ✅ Documentación completa

### 🚀 Listo para Producción
- 🔧 Backend robusto con manejo de errores
- 🌐 Frontend responsive y moderno
- 📊 Documentos profesionales listos para clientes
- 🧮 Calculadoras precisas con precios AWS
- 📁 Gestión completa de archivos
- 🔐 Seguridad con URLs presignadas
- ⚡ Performance optimizado

## 🔗 Enlaces Importantes

- **Repositorio**: https://github.com/coedaniel/bedrock-mcp-backend-multi-herramienta
- **Frontend Local**: http://localhost:3000
- **API Backend**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

---

## 🎯 ¡Sistema Completo y Funcional!

El **Bedrock MCP Backend v2.0** está completamente implementado con todas las funcionalidades solicitadas:

1. ✅ **Solución S3** - File Handler avanzado
2. ✅ **Soporte DOCX/XLSX** - Generadores profesionales
3. ✅ **Calculadora AWS** - Con guía paso a paso
4. ✅ **SOW Generator** - Documentos completos
5. ✅ **Frontend Web** - Interface interactiva

**¡Listo para usar en producción!** 🚀
