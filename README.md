# 🚀 Bedrock MCP Backend - Amazon Q CLI Style

Sistema completo que simula **Amazon Q Developer CLI** usando **Amazon Bedrock** + **MCP Servers** + **Function Calling**.

## 🏗️ Arquitectura

```
Frontend (Bedrock Playground) 
    ↓ Converse API + Function Calling
Backend (Amazon Q CLI simulado)
    ↓ Tool Use / Tool Result  
MCP Servers (Core, Diagrams, Docs, CloudFormation)
    ↓ Archivos generados
S3 (Almacenamiento automático)
```

## ✨ Características

### 🎯 **Frontend - Bedrock Playground Style**
- Interface de chat como el playground oficial de Bedrock
- Integración nativa con **Bedrock Converse API**
- Soporte completo para **Function Calling**
- Manejo automático de `tool_use` y `tool_result`

### 🔧 **Backend - Amazon Q CLI Style**
- Procesa herramientas MCP dinámicamente
- Filtrado inteligente de herramientas permitidas
- Subida automática de archivos a S3
- URLs presignadas para descarga segura

### 🛠️ **Herramientas MCP Disponibles**

#### **Core**
- `prompt_understanding` - Análisis de prompts complejos

#### **Diagramas AWS**
- `generate_diagram` - Diagramas con iconos oficiales AWS
- `list_icons` - Lista de iconos disponibles
- `get_diagram_examples` - Ejemplos de diagramas

#### **Documentación AWS**
- `search_documentation` - Búsqueda en docs oficiales
- `read_documentation` - Lectura de páginas específicas
- `recommend` - Recomendaciones de contenido

#### **CloudFormation**
- `generate_template` - Templates YAML
- `create_resource` - Recursos específicos
- `list_resources` - Lista de recursos disponibles

#### **Pricing (Interno)**
- Calculadoras de costos AWS (XLSX)
- Estimaciones multi-servicio
- Hojas de cálculo profesionales

## 🚀 Instalación y Uso

### **1. Clonar el repositorio**
```bash
git clone https://github.com/coedaniel/bedrock-mcp-backend-multi-herramienta.git
cd bedrock-mcp-backend-multi-herramienta
```

### **2. Configurar el backend**
```bash
cd bedrock-mcp-backend
pip install -r requirements.txt

# Configurar variables de entorno
export AWS_REGION=us-east-1
export S3_BUCKET=tu-bucket-s3
export MCP_BASE_URL=https://mcp.danielingram.shop/bedrock/tool-use
```

### **3. Iniciar el backend**
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### **4. Configurar el frontend**
```bash
cd ../frontend

# Configurar credenciales AWS en bedrock-client.js
# (En producción usar Cognito Identity Pool)
```

### **5. Acceder al sistema**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Function Definitions**: http://localhost:8000/bedrock/function-definitions

## 💡 Casos de Uso

### **🏗️ Arquitecto de Soluciones AWS**
```
Usuario: "Actúa como arquitecto de soluciones AWS. Necesito migrar 100 VMs a AWS."

Sistema:
1. Usa prompt_understanding para analizar requerimientos
2. Genera diagrama de arquitectura con generate_diagram  
3. Crea calculadora de costos automáticamente
4. Busca mejores prácticas con search_documentation
5. Genera template CloudFormation con generate_template
6. Sube todos los archivos a S3 organizadamente
```

### **📊 Generación de Diagramas**
```javascript
// El sistema automáticamente llama a:
{
  "name": "generate_diagram",
  "input": {
    "code": "with Diagram('AWS Architecture'):\n  ec2 = EC2('Web Server')\n  rds = RDS('Database')",
    "project_name": "mi-proyecto"
  }
}
```

### **💰 Calculadoras de Costos**
```bash
curl -X POST /documents/calculator/generate \
  -d '{
    "project_name": "Mi Proyecto",
    "compute_requirements": {
      "ec2_instances": [{"type": "t3.medium", "count": 2}]
    }
  }'
```

## 🔧 Configuración Avanzada

### **Variables de Entorno**
```bash
# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET=mi-bucket-s3

# MCP Configuration  
MCP_BASE_URL=https://mcp.danielingram.shop/bedrock/tool-use

# Security
USE_PRESIGNED_URLS=true
PRESIGNED_URL_EXPIRATION=3600

# Logging
LOG_LEVEL=INFO
```

### **Herramientas Permitidas**
Editar `allowed_tools.py` para personalizar las herramientas disponibles:

```python
ALLOWED_TOOLS = {
    'core': ['prompt_understanding'],
    'diagrams': ['generate_diagram', 'list_icons'],
    'documentation': ['search_documentation'],
    'cloudformation': ['generate_template']
}
```

## 🌐 Despliegue en Producción

### **Con Load Balancer + SSL**
```bash
# Desplegar infraestructura
aws cloudformation deploy \
  --template-file infrastructure/bedrock-mcp-infrastructure.yaml \
  --stack-name bedrock-mcp-prod \
  --capabilities CAPABILITY_IAM
```

### **URLs de Producción**
- **Frontend**: https://bedrock-mcp.danielingram.shop
- **Backend**: https://bedrock-mcp.danielingram.shop/api
- **Docs**: https://bedrock-mcp.danielingram.shop/docs

## 📚 Documentación

- [Arquitectura del Sistema](docs/ARCHITECTURE.md)
- [Referencia de API](docs/API_REFERENCE.md)
- [Guía de Despliegue](docs/DEPLOYMENT.md)

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

## 🆘 Soporte

- **Issues**: [GitHub Issues](https://github.com/coedaniel/bedrock-mcp-backend-multi-herramienta/issues)
- **Documentación**: [Wiki](https://github.com/coedaniel/bedrock-mcp-backend-multi-herramienta/wiki)
- **Email**: soporte@danielingram.shop

---

**Desarrollado con ❤️ para la comunidad AWS**
