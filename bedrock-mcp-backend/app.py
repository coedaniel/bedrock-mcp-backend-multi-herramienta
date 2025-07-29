# app.py - Backend Multi-Herramienta Bedrock MCP con File Handler Avanzado
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import json
import logging
import uuid
from datetime import datetime
from mcp_client import call_mcp_tool
from s3_utils import list_project_files
from file_handler import file_handler
from document_endpoints import router as document_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bedrock MCP Backend",
    description="Backend multi-herramienta para Bedrock Function Calling + MCP + S3",
    version="2.0.0"
)

# Incluir router de documentos
app.include_router(document_router)

@app.post("/bedrock/tool-use")
async def bedrock_tool_use(request: Request):
    """
    🔧 Endpoint principal para Bedrock Function Calling
    Procesa herramientas MCP dinámicamente con file handling avanzado
    """
    start_time = datetime.now()
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(f"🚀 Nueva solicitud - ID: {request_id}")
    
    try:
        # 1️⃣ Parsear request de Bedrock
        body = await request.json()
        logger.info(f"📥 Request recibido: {json.dumps(body, indent=2)}")
        
        # Extraer información de la herramienta
        tool_use = body.get("toolUse", {})
        tool_name = tool_use.get("name", "unknown")
        tool_id = tool_use.get("toolUseId", "unknown")
        tool_input = tool_use.get("input", {})
        
        # Extraer proyecto (con fallback)
        project_name = tool_input.get("project_name", "default")
        
        logger.info(f"🔧 Herramienta: {tool_name}")
        logger.info(f"🆔 Tool ID: {tool_id}")
        logger.info(f"📋 Proyecto: {project_name}")
        logger.info(f"📝 Input: {json.dumps(tool_input, indent=2)}")
        
        # 2️⃣ Llamar a MCP Tool
        logger.info(f"📡 Llamando a MCP server...")
        result_data = await call_mcp_tool(tool_name, tool_input)
        
        if not result_data:
            raise Exception("No se recibió respuesta del MCP server")
        
        logger.info(f"✅ Respuesta MCP recibida")
        logger.debug(f"📄 Respuesta MCP: {json.dumps(result_data, indent=2)}")
        
        # 3️⃣ Procesar respuesta con File Handler avanzado
        logger.info(f"🗂️ Procesando archivos con File Handler...")
        processed_response = await file_handler.process_mcp_response(result_data, project_name)
        
        # 4️⃣ Construir respuesta para Bedrock
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Verificar archivos procesados
        files_processed = processed_response.get('_files_processed', [])
        
        content = []
        
        if files_processed:
            # Respuesta con archivos procesados
            content.extend([
                {"text": f"✅ {tool_name} ejecutado exitosamente"},
                {"text": f"📁 {len(files_processed)} archivo(s) procesado(s) y subido(s) a S3"},
                {"text": f"📋 Proyecto: {project_name}"},
                {"text": f"⏱️ Tiempo: {processing_time:.2f}s"}
            ])
            
            # Agregar detalles de cada archivo
            for file_info in files_processed:
                file_detail = f"📄 **{file_info['filename']}**"
                file_detail += f"\n   • Tamaño: {file_info['size_bytes']:,} bytes"
                file_detail += f"\n   • Tipo: {file_info['content_type']}"
                
                if file_info.get('presigned_url'):
                    file_detail += f"\n   • 🔗 [Descargar]({file_info['presigned_url']})"
                else:
                    file_detail += f"\n   • 📍 S3: {file_info['s3_key']}"
                
                content.append({"text": file_detail})
            
            logger.info(f"📤 {len(files_processed)} archivo(s) procesado(s) exitosamente")
            
        else:
            # Respuesta informativa sin archivos
            response_text = processed_response.get("raw_text")
            if not response_text:
                # Buscar texto en diferentes formatos de respuesta
                if isinstance(processed_response, dict):
                    response_text = (
                        processed_response.get("message") or
                        processed_response.get("result") or
                        processed_response.get("output") or
                        json.dumps(processed_response, indent=2)
                    )
                else:
                    response_text = str(processed_response)
            
            content.extend([
                {"text": f"✅ {tool_name} ejecutado exitosamente"},
                {"text": response_text},
                {"text": f"📋 Proyecto: {project_name}"},
                {"text": f"⏱️ Tiempo: {processing_time:.2f}s"}
            ])
            logger.info(f"ℹ️ Respuesta informativa enviada")
        
        # Construir respuesta final
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

@app.get("/health")
async def health_check():
    """
    🏥 Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Bedrock MCP Backend",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Dynamic MCP Tool Processing",
            "Advanced File Handler",
            "S3 Auto-Upload",
            "Presigned URLs",
            "Multi-format Support"
        ]
    }

@app.get("/")
async def root():
    """
    🏠 Endpoint raíz con información del servicio
    """
    return {
        "service": "Bedrock MCP Backend",
        "description": "Backend multi-herramienta para Bedrock Function Calling + MCP + S3",
        "version": "2.0.0",
        "features": {
            "file_handler": "Advanced file detection and processing",
            "s3_integration": "Automatic upload with presigned URLs",
            "multi_format": "PNG, SVG, DOCX, XLSX, PDF, TXT support",
            "project_organization": "Files organized by project"
        },
        "endpoints": {
            "health": "/health",
            "tool_use": "/bedrock/tool-use",
            "list_files": "/projects/{project_name}/files"
        },
        "documentation": "https://github.com/coedaniel/bedrock-mcp-backend-multi-herramienta"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
