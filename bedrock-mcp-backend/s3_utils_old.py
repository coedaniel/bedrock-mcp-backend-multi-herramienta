# s3_utils.py
import boto3
import uuid
import os
import logging
from datetime import datetime
from config import AWS_REGION, S3_BUCKET, CONTENT_TYPES, USE_PRESIGNED_URLS, PRESIGNED_URL_EXPIRATION

logger = logging.getLogger(__name__)

s3 = boto3.client("s3", region_name=AWS_REGION)

def upload_to_s3(filename: str, content: bytes, project_name: str = None, tool_name: str = None) -> str:
    """
    Sube archivo a S3 con estructura de carpetas por proyecto y URLs presignadas.
    """
    logger.info(f"📤 Iniciando subida a S3: {filename}")
    
    # Determinar content-type
    ext = filename.split(".")[-1].lower() if "." in filename else "txt"
    content_type = CONTENT_TYPES.get(ext, "application/octet-stream")
    logger.debug(f"📋 Content-Type detectado: {content_type}")
    
    # Estructura de carpetas por proyecto
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_folder = project_name or "general"
    tool_folder = tool_name or "misc"
    
    key = f"arquitecturas/{project_folder}/{tool_folder}/{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
    logger.info(f"🗂️ Ruta S3: s3://{S3_BUCKET}/{key}")
    
    try:
        # Metadata adicional
        metadata = {
            "project": project_folder,
            "tool": tool_folder,
            "timestamp": timestamp,
            "original_filename": filename
        }
        
        # Subir archivo
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata=metadata
        )
        
        logger.info(f"✅ Archivo subido exitosamente a S3")
        
        # Generar URL (presignada o pública)
        if USE_PRESIGNED_URLS:
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': key},
                ExpiresIn=PRESIGNED_URL_EXPIRATION
            )
            logger.info(f"🔐 URL presignada generada (expira en {PRESIGNED_URL_EXPIRATION}s)")
        else:
            url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
            logger.info(f"🌐 URL pública generada")
        
        return url
        
    except Exception as e:
        logger.error(f"❌ Error subiendo a S3: {str(e)}")
        raise Exception(f"Error uploading to S3: {str(e)}")

def generate_presigned_url(s3_key: str, expiration: int = None) -> str:
    """
    Genera URL presignada para descarga de archivo S3
    """
    if not USE_PRESIGNED_URLS:
        return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
    
    try:
        expiration = expiration or PRESIGNED_URL_EXPIRATION
        
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=expiration
        )
        
        logger.info(f"🔗 URL presignada generada para: {s3_key}")
        return presigned_url
        
    except Exception as e:
        logger.error(f"❌ Error generando URL presignada: {str(e)}")
        return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

def list_project_files(project_name: str, limit: int = 10) -> list:
    """
    Lista archivos de un proyecto específico.
    """
    logger.info(f"📋 Listando archivos del proyecto: {project_name}")
    
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=f"arquitecturas/{project_name}/",
            MaxKeys=limit
        )
        
        files = []
        for obj in response.get('Contents', []):
            files.append({
                "key": obj['Key'],
                "size": obj['Size'],
                "last_modified": obj['LastModified'].isoformat(),
                "url": f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{obj['Key']}"
            })
        
        logger.info(f"📁 Encontrados {len(files)} archivos")
        return files
        
    except Exception as e:
        logger.error(f"❌ Error listando archivos: {str(e)}")
        return []
