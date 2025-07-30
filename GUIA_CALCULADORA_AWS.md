# 🧮 Guía Paso a Paso: Calculadora AWS Oficial

## 📋 Índice
1. [Introducción](#introducción)
2. [Preparación](#preparación)
3. [Uso de la Calculadora Web](#uso-de-la-calculadora-web)
4. [Generación via API](#generación-via-api)
5. [Personalización Avanzada](#personalización-avanzada)
6. [Mejores Prácticas](#mejores-prácticas)
7. [Troubleshooting](#troubleshooting)

## 🎯 Introducción

La **Calculadora AWS** integrada en nuestro sistema permite generar hojas de cálculo profesionales en formato XLSX con estimaciones de costos precisas para proyectos AWS.

### ✨ Características Principales:
- 📊 **Múltiples hojas especializadas**: Compute, Storage, Database, Networking
- 🧮 **Fórmulas automáticas**: Cálculos dinámicos en tiempo real
- 💰 **Precios actualizados**: Basados en tarifas oficiales AWS
- 📈 **Proyecciones**: Costos mensuales y anuales
- 🎨 **Formato profesional**: Listo para presentaciones

## 🛠️ Preparación

### Requisitos Previos:
- ✅ Backend MCP ejecutándose en puerto 8000
- ✅ Frontend web ejecutándose en puerto 3000
- ✅ Conexión a internet para APIs AWS
- ✅ Navegador web moderno

### Verificar Sistema:
```bash
# Verificar backend
curl http://localhost:8000/health

# Verificar frontend
curl http://localhost:3000
```

## 🌐 Uso de la Calculadora Web

### Paso 1: Acceder a la Interface
1. Abrir navegador en `http://localhost:3000`
2. Hacer clic en la pestaña **"🧮 Calculadora AWS"**

### Paso 2: Configuración Básica
```
📋 Nombre del Proyecto: "Mi Proyecto AWS"
🌍 Región AWS: us-east-1 (seleccionar según necesidad)
```

### Paso 3: Definir Requerimientos
En el campo **"Requerimientos Adicionales"**, usar formato JSON:

#### Ejemplo Básico:
```json
{
  "compute_requirements": {
    "ec2_instances": [
      {"type": "t3.medium", "quantity": 2, "hours_per_month": 730}
    ]
  },
  "storage_requirements": {
    "s3_storage": [
      {"class": "Standard", "gb": 100}
    ]
  },
  "database_requirements": {
    "rds_instances": [
      {"engine": "MySQL", "type": "db.t3.micro", "quantity": 1}
    ]
  }
}
```

#### Ejemplo Avanzado:
```json
{
  "compute_requirements": {
    "ec2_instances": [
      {"type": "t3.medium", "quantity": 2, "hours_per_month": 730},
      {"type": "t3.large", "quantity": 1, "hours_per_month": 730}
    ],
    "lambda_functions": {
      "requests_per_month": 1000000,
      "avg_duration_ms": 200,
      "memory_mb": 512
    }
  },
  "storage_requirements": {
    "s3_storage": [
      {"class": "Standard", "gb": 500},
      {"class": "Standard-IA", "gb": 1000},
      {"class": "Glacier", "gb": 5000}
    ],
    "ebs_volumes": [
      {"type": "gp3", "size_gb": 100, "quantity": 3}
    ]
  },
  "database_requirements": {
    "rds_instances": [
      {"engine": "MySQL", "type": "db.t3.small", "quantity": 1},
      {"engine": "PostgreSQL", "type": "db.r5.large", "quantity": 1}
    ]
  },
  "networking_requirements": {
    "cloudfront": {
      "data_transfer_gb": 1000,
      "requests": 10000000
    },
    "load_balancer": {
      "type": "ALB",
      "quantity": 2
    }
  }
}
```

### Paso 4: Generar Calculadora
1. Hacer clic en **"🧮 Generar Calculadora"**
2. Esperar procesamiento (5-10 segundos)
3. Descargar archivo XLSX generado

## 🔧 Generación via API

### Endpoint Principal:
```
POST http://localhost:8000/documents/calculator/generate
```

### Ejemplo con cURL:
```bash
curl -X POST "http://localhost:8000/documents/calculator/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Proyecto API",
    "region": "us-east-1",
    "compute_requirements": {
      "ec2_instances": [
        {"type": "t3.medium", "quantity": 2, "hours_per_month": 730}
      ]
    }
  }'
```

### Ejemplo con Python:
```python
import requests
import json

url = "http://localhost:8000/documents/calculator/generate"
data = {
    "project_name": "Mi Calculadora",
    "region": "us-east-1",
    "compute_requirements": {
        "ec2_instances": [
            {"type": "t3.medium", "quantity": 2, "hours_per_month": 730}
        ]
    },
    "storage_requirements": {
        "s3_storage": [
            {"class": "Standard", "gb": 100}
        ]
    }
}

response = requests.post(url, json=data)
result = response.json()

if response.status_code == 200:
    print(f"✅ Calculadora generada: {result['filename']}")
    print(f"🔗 Descargar: {result['presigned_url']}")
else:
    print(f"❌ Error: {result}")
```

## 🎨 Personalización Avanzada

### Modificar Precios por Región:
```json
{
  "region": "eu-west-1",
  "custom_pricing": {
    "ec2": {
      "t3.medium": 0.0464
    },
    "s3": {
      "standard": 0.0245
    }
  }
}
```

### Agregar Servicios Personalizados:
```json
{
  "custom_services": {
    "ElastiCache": {
      "cache.t3.micro": {
        "price_per_hour": 0.017,
        "quantity": 1
      }
    },
    "CloudWatch": {
      "custom_metrics": {
        "price_per_metric": 0.30,
        "quantity": 100
      }
    }
  }
}
```

## 📊 Estructura del Archivo XLSX Generado

### Hoja 1: Resumen
- 📋 Información del proyecto
- 💰 Totales por categoría
- 📈 Costo mensual y anual

### Hoja 2: Compute
- 🖥️ Instancias EC2
- ⚡ AWS Lambda
- 🔄 Auto Scaling

### Hoja 3: Storage
- 🗄️ Amazon S3 (todas las clases)
- 💾 EBS Volumes
- 📦 EFS File Systems

### Hoja 4: Database
- 🗃️ Amazon RDS
- ⚡ DynamoDB
- 🔍 ElastiCache

### Hoja 5: Networking
- 🌐 CloudFront
- ⚖️ Load Balancers
- 🔗 Data Transfer

## 💡 Mejores Prácticas

### 1. Estimación Precisa:
```json
{
  "compute_requirements": {
    "ec2_instances": [
      {
        "type": "t3.medium",
        "quantity": 2,
        "hours_per_month": 730,
        "utilization": 0.8,
        "reserved_instance": true
      }
    ]
  }
}
```

### 2. Considerar Escalabilidad:
```json
{
  "scaling_scenarios": {
    "current": {"instances": 2},
    "peak": {"instances": 5},
    "projected_6_months": {"instances": 8}
  }
}
```

### 3. Incluir Costos Ocultos:
```json
{
  "additional_costs": {
    "data_transfer": {"gb_per_month": 1000},
    "backup_storage": {"gb_per_month": 500},
    "monitoring": {"custom_metrics": 50}
  }
}
```

## 🔍 Troubleshooting

### Error: "python-docx no está instalado"
```bash
pip install python-docx openpyxl
```

### Error: "No se pudo subir a S3"
1. Verificar credenciales AWS
2. Verificar permisos del bucket
3. Verificar configuración en `config.py`

### Error: "Formato JSON inválido"
- Usar validador JSON online
- Verificar comillas y comas
- Usar template de ejemplo

### Calculadora vacía o con errores:
1. Verificar tipos de instancia válidos
2. Confirmar región AWS soportada
3. Revisar logs del backend

## 📞 Soporte

### Logs del Sistema:
```bash
# Ver logs del backend
tail -f /home/ec2-user/bedrock-mcp-backend-complete/bedrock-mcp-backend/app.log

# Ver logs específicos de documentos
grep "Calculadora" /home/ec2-user/bedrock-mcp-backend-complete/bedrock-mcp-backend/app.log
```

### Endpoints de Ayuda:
- `GET /documents/calculator/template` - Template de ejemplo
- `GET /health` - Estado del sistema
- `GET /` - Información general

### Contacto:
- 📧 Soporte técnico via logs del sistema
- 📋 Issues en GitHub del proyecto
- 🔧 Documentación en `/docs`

---

## 🎉 ¡Listo para Usar!

Tu calculadora AWS está configurada y lista para generar estimaciones profesionales. Sigue esta guía paso a paso y tendrás hojas de cálculo detalladas en minutos.

**Próximos pasos sugeridos:**
1. Generar tu primera calculadora de prueba
2. Personalizar con tus servicios específicos
3. Integrar con tu flujo de trabajo de cotizaciones
4. Automatizar generación para propuestas recurrentes
