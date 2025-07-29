# s3_utils.py - Utilidades S3 actualizadas para compatibilidad con File Handler
import boto3
import uuid
import os
import logging
from datetime import datetime
from typing import Union, Optional
from config import AWS_REGION, S3_BUCKET, CONTENT_TYPES, USE_PRESIGNED_URLS, PRESIGNED_URL_EXPIRATION

logger = logging.getLogger(__name__)

s3 = boto3.client("s3", region_name=AWS_REGION)

async def upload_to_s3(
    content: bytes, 
    key: str, 
    content_type: str = "application/octet-stream",
    filename: str = None,
    project_name: str = None, 
    tool_name: str = None
) -> Optional[str]:
    """
    Sube archivo a S3 - Versión async compatible con File Handler
    
    Args:
        content: Contenido del archivo en bytes
        key: Clave S3 (si se proporciona, se usa directamente)
        content_type: Tipo de contenido MIME
        filename: Nombre original del archivo (para compatibilidad)
        project_name: Nombre del proyecto (para compatibilidad)
        tool_name: Nombre de la herramienta (para compatibilidad)
    
    Returns:
        URL del archivo subido o None si hay error
    """
    logger.info(f"📤 Iniciando subida a S3: {key}")
    
    try:
        # Metadata adicional
        metadata = {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "upload_method": "file_handler"
        }
        
        if filename:
            metadata["original_filename"] = filename
        if project_name:
            metadata["project"] = project_name
        if tool_name:
            metadata["tool"] = tool_name
        
        # Subir archivo
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata=metadata
        )
        
        # Generar URL
        s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
        
        logger.info(f"✅ Archivo subido exitosamente a S3: {s3_url}")
        return s3_url
        
    except Exception as e:
        logger.error(f"❌ Error subiendo archivo a S3: {str(e)}")
        return None

def upload_to_s3_sync(filename: str, content: bytes, project_name: str = None, tool_name: str = None) -> str:
    """
    Versión síncrona para compatibilidad con código existente
    """
    logger.info(f"📤 Iniciando subida a S3 (sync): {filename}")
    
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
            "original_filename": filename,
            "upload_method": "legacy"
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
        
        # Generar URL presignada si está habilitado
        if USE_PRESIGNED_URLS:
            try:
                presigned_url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': key},
                    ExpiresIn=PRESIGNED_URL_EXPIRATION
                )
                logger.info(f"🔗 URL presignada generada")
                return presigned_url
            except Exception as e:
                logger.error(f"⚠️ Error generando URL presignada: {str(e)}")
                return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
        else:
            return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
            
    except Exception as e:
        logger.error(f"❌ Error subiendo archivo a S3: {str(e)}")
        return None

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
    Lista archivos de un proyecto específico en S3
    """
    logger.info(f"📋 Listando archivos del proyecto: {project_name}")
    
    try:
        # Buscar en diferentes prefijos
        prefixes = [
            f"arquitecturas/{project_name}/",
            f"documentos/{project_name}/",
            f"calculadoras/{project_name}/",
            f"archivos/{project_name}/"
        ]
        
        all_files = []
        
        for prefix in prefixes:
            try:
                response = s3.list_objects_v2(
                    Bucket=S3_BUCKET,
                    Prefix=prefix,
                    MaxKeys=limit
                )
                
                if 'Contents' in response:
                    for obj in response['Contents']:
                        file_info = {
                            "key": obj['Key'],
                            "filename": obj['Key'].split('/')[-1],
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat(),
                            "url": generate_presigned_url(obj['Key']) if USE_PRESIGNED_URLS else f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{obj['Key']}"
                        }
                        all_files.append(file_info)
                        
            except Exception as e:
                logger.debug(f"No se encontraron archivos en {prefix}: {str(e)}")
                continue
        
        # Ordenar por fecha de modificación (más reciente primero)
        all_files.sort(key=lambda x: x['last_modified'], reverse=True)
        
        # Limitar resultados
        result = all_files[:limit]
        
        logger.info(f"📁 Encontrados {len(result)} archivos para el proyecto {project_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error listando archivos del proyecto {project_name}: {str(e)}")
        return []
