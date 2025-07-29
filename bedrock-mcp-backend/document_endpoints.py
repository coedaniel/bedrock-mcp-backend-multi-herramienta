"""
📄 Document Endpoints - Endpoints para generar SOW y Calculadoras
Integra con el backend principal para generar documentos especializados
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import uuid

from document_processors import generate_sow_document, generate_aws_calculator
from s3_utils import upload_to_s3, generate_presigned_url

logger = logging.getLogger(__name__)

# Router para endpoints de documentos
router = APIRouter(prefix="/documents", tags=["documents"])

# Modelos Pydantic
class SOWRequest(BaseModel):
    project_name: str
    client_name: Optional[str] = "Cliente"
    objective: Optional[str] = None
    scopes: Optional[List[str]] = None
    out_of_scope: Optional[List[str]] = None
    architecture: Optional[str] = None
    aws_services: Optional[List[str]] = None
    cost_estimation: Optional[Dict[str, Any]] = None
    activities: Optional[List[Dict[str, Any]]] = None
    conclusions: Optional[List[str]] = None
    appendices: Optional[List[str]] = None
    version: Optional[str] = "1.0"
    responsible: Optional[str] = "AWS Solutions Architect"

class CalculatorRequest(BaseModel):
    project_name: str
    region: Optional[str] = "us-east-1"
    compute_requirements: Optional[Dict[str, Any]] = None
    storage_requirements: Optional[Dict[str, Any]] = None
    database_requirements: Optional[Dict[str, Any]] = None
    networking_requirements: Optional[Dict[str, Any]] = None

@router.post("/sow/generate")
async def generate_sow(request: SOWRequest):
    """
    📋 Genera Statement of Work (SOW) en formato DOCX
    """
    start_time = datetime.now()
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"📋 Generando SOW - ID: {request_id}")
    logger.info(f"📋 Proyecto: {request.project_name}")
    
    try:
        # Preparar datos del proyecto
        project_data = {
            'project_name': request.project_name,
            'client_name': request.client_name,
            'objective': request.objective,
            'scopes': request.scopes,
            'out_of_scope': request.out_of_scope,
            'architecture': request.architecture,
            'aws_services': request.aws_services,
            'cost_estimation': request.cost_estimation,
            'activities': request.activities,
            'conclusions': request.conclusions,
            'appendices': request.appendices,
            'version': request.version,
            'responsible': request.responsible
        }
        
        # Generar documento SOW
        logger.info(f"🔄 Generando documento DOCX...")
        sow_bytes = generate_sow_document(project_data)
        
        # Generar nombre único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"SOW_{request.project_name}_{timestamp}_{unique_id}.docx"
        
        # Subir a S3
        logger.info(f"📤 Subiendo a S3...")
        s3_key = f"documentos/{request.project_name}/sow/{filename}"
        s3_url = await upload_to_s3(
            content=sow_bytes,
            key=s3_key,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        if not s3_url:
            raise Exception("Error subiendo documento a S3")
        
        # Generar URL presignada
        presigned_url = generate_presigned_url(s3_key)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ SOW generado exitosamente - ID: {request_id}")
        logger.info(f"⏱️ Tiempo: {processing_time:.2f}s")
        
        return {
            "success": True,
            "request_id": request_id,
            "document_type": "SOW",
            "project_name": request.project_name,
            "filename": filename,
            "s3_key": s3_key,
            "s3_url": s3_url,
            "presigned_url": presigned_url,
            "size_bytes": len(sow_bytes),
            "processing_time": processing_time,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        
        logger.error(f"💥 Error generando SOW {request_id}: {error_msg}")
        logger.error(f"⏱️ Tiempo hasta error: {processing_time:.2f}s")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error generando SOW",
                "message": error_msg,
                "request_id": request_id,
                "processing_time": processing_time
            }
        )

@router.post("/calculator/generate")
async def generate_calculator(request: CalculatorRequest):
    """
    🧮 Genera Calculadora AWS en formato XLSX
    """
    start_time = datetime.now()
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"🧮 Generando Calculadora AWS - ID: {request_id}")
    logger.info(f"📋 Proyecto: {request.project_name}")
    
    try:
        # Preparar datos de la calculadora
        calculator_data = {
            'project_name': request.project_name,
            'region': request.region,
            'compute_requirements': request.compute_requirements,
            'storage_requirements': request.storage_requirements,
            'database_requirements': request.database_requirements,
            'networking_requirements': request.networking_requirements
        }
        
        # Generar calculadora
        logger.info(f"🔄 Generando calculadora XLSX...")
        calculator_bytes = generate_aws_calculator(calculator_data)
        
        # Generar nombre único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"AWS_Calculator_{request.project_name}_{timestamp}_{unique_id}.xlsx"
        
        # Subir a S3
        logger.info(f"📤 Subiendo a S3...")
        s3_key = f"calculadoras/{request.project_name}/{filename}"
        s3_url = await upload_to_s3(
            content=calculator_bytes,
            key=s3_key,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        if not s3_url:
            raise Exception("Error subiendo calculadora a S3")
        
        # Generar URL presignada
        presigned_url = generate_presigned_url(s3_key)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Calculadora generada exitosamente - ID: {request_id}")
        logger.info(f"⏱️ Tiempo: {processing_time:.2f}s")
        
        return {
            "success": True,
            "request_id": request_id,
            "document_type": "AWS_Calculator",
            "project_name": request.project_name,
            "filename": filename,
            "s3_key": s3_key,
            "s3_url": s3_url,
            "presigned_url": presigned_url,
            "size_bytes": len(calculator_bytes),
            "processing_time": processing_time,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        
        logger.error(f"💥 Error generando calculadora {request_id}: {error_msg}")
        logger.error(f"⏱️ Tiempo hasta error: {processing_time:.2f}s")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error generando calculadora",
                "message": error_msg,
                "request_id": request_id,
                "processing_time": processing_time
            }
        )

@router.get("/sow/template")
async def get_sow_template():
    """
    📋 Obtiene template de ejemplo para SOW
    """
    return {
        "template": {
            "project_name": "Migración a AWS Cloud",
            "client_name": "Empresa XYZ",
            "objective": "Migrar la infraestructura on-premise a AWS para mejorar escalabilidad y reducir costos",
            "scopes": [
                "Análisis de infraestructura actual",
                "Diseño de arquitectura AWS",
                "Migración de aplicaciones críticas",
                "Configuración de monitoreo",
                "Documentación y capacitación"
            ],
            "out_of_scope": [
                "Desarrollo de nuevas funcionalidades",
                "Migración de sistemas legacy no compatibles",
                "Soporte post-implementación"
            ],
            "architecture": "Arquitectura multi-tier con alta disponibilidad usando servicios AWS nativos",
            "aws_services": [
                "Amazon EC2 - Instancias de aplicación",
                "Amazon RDS - Base de datos",
                "Amazon S3 - Almacenamiento",
                "Amazon CloudFront - CDN",
                "AWS Lambda - Funciones serverless",
                "Amazon CloudWatch - Monitoreo"
            ],
            "cost_estimation": {
                "EC2": {
                    "monthly_cost": 150.00,
                    "description": "2 instancias t3.medium"
                },
                "RDS": {
                    "monthly_cost": 50.00,
                    "description": "1 instancia db.t3.small"
                },
                "S3": {
                    "monthly_cost": 25.00,
                    "description": "1TB almacenamiento"
                }
            },
            "activities": [
                {
                    "phase": "Fase 1: Análisis",
                    "duration": "2 semanas",
                    "tasks": [
                        "Análisis de requerimientos",
                        "Diseño de arquitectura",
                        "Plan de migración"
                    ]
                }
            ],
            "conclusions": [
                "Reducción estimada de costos del 30%",
                "Mejora en escalabilidad y disponibilidad",
                "Implementación en 6 semanas"
            ]
        }
    }

@router.get("/calculator/template")
async def get_calculator_template():
    """
    🧮 Obtiene template de ejemplo para Calculadora
    """
    return {
        "template": {
            "project_name": "Proyecto AWS",
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
            },
            "database_requirements": {
                "rds_instances": [
                    {"engine": "MySQL", "type": "db.t3.micro", "quantity": 1}
                ]
            },
            "networking_requirements": {
                "cloudfront": {
                    "data_transfer_gb": 100
                }
            }
        }
    }
