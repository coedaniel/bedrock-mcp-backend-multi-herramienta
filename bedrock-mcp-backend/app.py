# app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import json
import base64
import binascii
import logging
import uuid
import requests
from datetime import datetime
from mcp_client import call_mcp_tool
from s3_utils import upload_to_s3, list_project_files

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bedrock MCP Backend",
    description="Backend multi-herramienta para Bedrock Function Calling + MCP + S3",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "bedrock-mcp-backend",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/bedrock/tool-use")
async def handle_tool_use(request: Request):
    """
    🚀 Backend Bedrock Function Calling → MCP → S3
    Procesa cualquier tool_use de Bedrock automáticamente
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    logger.info(f"🎯 Nueva solicitud Bedrock - ID: {request_id}")
    
    try:
        body = await request.json()
        logger.debug(f"📥 Body recibido: {json.dumps(body, indent=2)}")
        
        tool_use = body.get("toolUse", {})
        tool_name = tool_use.get("name")
        tool_id = tool_use.get("toolUseId")
        tool_input = tool_use.get("input", {})
        conversation_id = body.get("conversationId")
        message_id = body.get("messageId")
        
        # Extraer nombre del proyecto si está disponible
        project_name = tool_input.get("project_name") or body.get("project_name") or "bedrock-auto"
        
        logger.info(f"🔧 Procesando herramienta: {tool_name}")
        logger.info(f"📋 Proyecto: {project_name}")
        logger.info(f"🆔 Tool ID: {tool_id}")
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing tool name")
        
        # 1️⃣ Llamar al MCP correspondiente
        logger.info(f"📡 Llamando MCP: {tool_name}")
        mcp_response = call_mcp_tool(tool_name, tool_input, conversation_id, message_id)
        result_data = mcp_response.get("result", {})
        
        logger.info(f"✅ MCP respondió exitosamente")
        logger.debug(f"📊 Datos resultado: {json.dumps(result_data, indent=2)}")
        
        # 2️⃣ Detectar formato y procesar archivo
        filename = result_data.get("filename") or result_data.get("path", "").split("/")[-1] or f"{tool_name}_{request_id[:8]}.txt"
        file_url = None
        file_processed = False
        
        logger.info(f"📄 Procesando archivo: {filename}")
        
        # 3️⃣ Obtener contenido según formato
        try:
            if "status" in result_data and result_data["status"] == "success":
                # Caso especial: herramientas que devuelven resultado exitoso
                logger.info(f"✅ Herramienta completada exitosamente: {result_data.get('message', 'Sin mensaje')}")
                
                # Verificar si ya tiene s3_url (desde el wrapper)
                if "s3_url" in result_data:
                    file_url = result_data.get("s3_url")
                    file_processed = True
                    logger.info(f"📤 Archivo ya subido a S3: {file_url}")
                elif "path" in result_data:
                    # Fallback: path local (caso anterior)
                    local_path = result_data.get("path", "")
                    logger.info(f"📁 Leyendo archivo local: {local_path}")
                    
                    # Intentar leer el archivo desde el MCP server
                    try:
                        file_request_url = f"https://mcp.danielingram.shop/files{local_path}"
                        logger.info(f"📥 Solicitando archivo: {file_request_url}")
                        
                        file_response = requests.get(file_request_url, timeout=30)
                        
                        if file_response.status_code == 200:
                            file_bytes = file_response.content
                            file_url = upload_to_s3(filename, file_bytes, project_name, tool_name)
                            file_processed = True
                            logger.info(f"📤 Archivo descargado y subido a S3: {file_url}")
                        else:
                            logger.warning(f"⚠️ No se pudo descargar archivo: {file_response.status_code}")
                            file_url = f"Archivo generado en: {local_path}"
                            file_processed = True
                            
                    except Exception as download_error:
                        logger.error(f"❌ Error descargando archivo: {str(download_error)}")
                        file_url = f"Archivo generado en: {local_path}"
                        file_processed = True
                else:
                    # Solo mensaje de éxito sin archivo
                    file_url = result_data.get("message", "Operación completada")
                    file_processed = True
                
            elif "diagram_data" in result_data:  # Diagramas en hex
                logger.info(f"🎨 Procesando diagrama (hex)")
                file_bytes = bytes.fromhex(result_data["diagram_data"])
                file_url = upload_to_s3(filename, file_bytes, project_name, tool_name)
                file_processed = True
                
            elif "file_content" in result_data:  # Archivos en base64
                logger.info(f"📁 Procesando archivo (base64)")
                file_bytes = base64.b64decode(result_data["file_content"])
                file_url = upload_to_s3(filename, file_bytes, project_name, tool_name)
                file_processed = True
                
            elif "raw_text" in result_data:  # Texto plano
                logger.info(f"📝 Procesando texto plano")
                file_bytes = result_data["raw_text"].encode("utf-8")
                if not filename.endswith(('.txt', '.md', '.json', '.yaml', '.yml')):
                    filename += ".txt"
                file_url = upload_to_s3(filename, file_bytes, project_name, tool_name)
                file_processed = True
                
            elif "data" in result_data:
                # Intentar hex genérico primero
                try:
                    logger.info(f"🔄 Intentando procesar como hex")
                    file_bytes = bytes.fromhex(result_data["data"])
                    file_url = upload_to_s3(filename, file_bytes, project_name, tool_name)
                    file_processed = True
                except binascii.Error:
                    logger.info(f"🔄 Procesando como texto")
                    file_bytes = result_data["data"].encode("utf-8")
                    if not filename.endswith(('.txt', '.md', '.json', '.yaml', '.yml')):
                        filename += ".txt"
                    file_url = upload_to_s3(filename, file_bytes, project_name, tool_name)
                    file_processed = True
            
            else:
                # Respuesta de solo texto/información
                logger.info(f"ℹ️ Respuesta informativa sin archivo")
                response_text = json.dumps(result_data, indent=2) if result_data else "Operación completada"
                file_processed = False
                
        except Exception as file_error:
            logger.error(f"❌ Error procesando archivo: {str(file_error)}")
            file_processed = False
        
        # 4️⃣ Construir respuesta para Bedrock
        processing_time = (datetime.now() - start_time).total_seconds()
        
        content = []
        
        if file_processed and file_url:
            content.extend([
                {"text": f"✅ {tool_name} ejecutado exitosamente"},
                {"text": f"📁 Archivo: {filename}"},
                {"text": f"🔗 URL: {file_url}"},
                {"text": f"📋 Proyecto: {project_name}"},
                {"text": f"⏱️ Tiempo: {processing_time:.2f}s"}
            ])
            logger.info(f"📤 Archivo subido: {file_url}")
        else:
            # Respuesta informativa
            response_text = result_data.get("raw_text") or json.dumps(result_data, indent=2)
            content.extend([
                {"text": f"✅ {tool_name} ejecutado exitosamente"},
                {"text": response_text},
                {"text": f"⏱️ Tiempo: {processing_time:.2f}s"}
            ])
            logger.info(f"ℹ️ Respuesta informativa enviada")
        
        response = {
            "toolResult": {
                "toolUseId": tool_id,
                "content": content
            }
        }
        
        logger.info(f"🎉 Solicitud completada exitosamente - ID: {request_id}")
        logger.info(f"⏱️ Tiempo total: {processing_time:.2f}s")
        
        return response
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        
        logger.error(f"💥 Error en solicitud {request_id}: {error_msg}")
        logger.error(f"⏱️ Tiempo hasta error: {processing_time:.2f}s")
        
        return {
            "toolResult": {
                "toolUseId": tool_id if 'tool_id' in locals() else "unknown",
                "content": [
                    {"text": f"❌ Error ejecutando {tool_name if 'tool_name' in locals() else 'herramienta'}: {error_msg}"},
                    {"text": f"🆔 Request ID: {request_id}"},
                    {"text": f"⏱️ Tiempo: {processing_time:.2f}s"}
                ]
            }
        }

@app.get("/projects/{project_name}/files")
async def list_files(project_name: str, limit: int = 10):
    """
    📋 Lista archivos de un proyecto específico
    """
    logger.info(f"📋 Listando archivos del proyecto: {project_name}")
    
    try:
        files = list_project_files(project_name, limit)
        return {
            "project": project_name,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"❌ Error listando archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """
    🏠 Endpoint raíz con información del servicio
    """
    return {
        "service": "Bedrock MCP Backend",
        "description": "Backend multi-herramienta para Bedrock Function Calling + MCP + S3",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tool_use": "/bedrock/tool-use",
            "list_files": "/projects/{project_name}/files"
        },
        "features": [
            "🔧 Soporte dinámico para cualquier herramienta MCP",
            "📁 Subida automática a S3 con estructura por proyecto",
            "🔐 URLs presignadas para seguridad",
            "📊 Logging detallado y auditoría completa",
            "🎨 Soporte multi-formato (PNG, SVG, CSV, XLSX, YAML, JSON, DOCX, TXT)"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Iniciando Bedrock MCP Backend")
    uvicorn.run(app, host="0.0.0.0", port=8000)
