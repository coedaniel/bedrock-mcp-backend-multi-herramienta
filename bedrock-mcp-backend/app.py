# app.py - Backend Bedrock MCP Enfocado (Core + Diagramas + Docs + CloudFormation)
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import json
import logging
import uuid
import time
from datetime import datetime
from mcp_client import call_mcp_tool
from s3_utils import list_project_files
from file_processor import FileProcessor
from document_endpoints import router as document_router
from allowed_tools import is_tool_allowed, get_all_categories, ALL_ALLOWED_TOOLS

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bedrock MCP Backend - Focused",
    description="Backend enfocado para Bedrock: Core + Diagramas + Documentación + CloudFormation + Pricing",
    version="2.2.0"
)

# Incluir router de documentos (para pricing/calculadoras)
app.include_router(document_router)

@app.post("/bedrock/tool-use")
async def bedrock_tool_use(request: Request):
    """
    🎯 Endpoint principal para tool-use de Bedrock (Solo herramientas permitidas)
    Procesa herramientas MCP enfocadas: Core + Diagramas + Docs + CloudFormation
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"🚀 Nueva solicitud Bedrock tool-use - ID: {request_id}")
    
    try:
        # Parsear request
        body = await request.json()
        logger.debug(f"📥 Request body: {json.dumps(body, indent=2)}")
        
        # Extraer información del tool use
        tool_use = body.get("toolUse", {})
        tool_name = tool_use.get("name", "unknown")
        tool_id = tool_use.get("toolUseId", request_id)
        tool_input = tool_use.get("input", {})
        
        # Verificar si la herramienta está permitida
        if not is_tool_allowed(tool_name):
            logger.warning(f"🚫 Herramienta no permitida: {tool_name}")
            return {
                "toolResult": {
                    "toolUseId": tool_id,
                    "content": [
                        {"text": f"❌ Herramienta '{tool_name}' no está disponible en este sistema"},
                        {"text": f"✅ Herramientas disponibles: {', '.join(ALL_ALLOWED_TOOLS)}"},
                        {"text": f"📋 Categorías: {', '.join(get_all_categories())}"},
                        {"text": f"🆔 Request ID: {request_id}"}
                    ]
                }
            }
        
        conversation_id = body.get("conversationId", f"conv-{request_id}")
        message_id = body.get("messageId", f"msg-{request_id}")
        
        logger.info(f"🔧 Ejecutando herramienta permitida: {tool_name}")
        logger.info(f"📋 Input: {json.dumps(tool_input, indent=2)}")
        
        # Llamar al MCP
        mcp_response = call_mcp_tool(
            tool_name=tool_name,
            arguments=tool_input,
            conversation_id=conversation_id,
            message_id=message_id
        )
        
        # Procesar archivos automáticamente con el nuevo procesador
        project_name = tool_input.get("project_name", "bedrock-mcp")
        file_processor = FileProcessor(project_name=project_name)
        
        result_data = mcp_response.get("result", {})
        processed_files = file_processor.process_mcp_response(tool_name, result_data)
        
        # Si no se encontraron archivos con el procesador principal, intentar múltiples archivos
        if not processed_files and result_data.get("raw_text"):
            processed_files = file_processor.process_multiple_files(
                result_data.get("raw_text", ""), 
                tool_name
            )
        
        # Construir respuesta
        content = []
        
        if processed_files:
            content.append({
                "text": f"✅ {tool_name} ejecutado exitosamente. {len(processed_files)} archivo(s) generado(s) y subido(s) a S3:"
            })
            
            for file_info in processed_files:
                content.append({
                    "text": f"📁 {file_info['filename']} ({file_info['file_type'].upper()}, {file_info['size_bytes']} bytes)"
                })
                content.append({
                    "text": f"🔗 URL S3: {file_info['presigned_url']}"
                })
        else:
            # Si no hay archivos, mostrar el resultado como texto
            raw_text = result_data.get("raw_text", "Herramienta ejecutada exitosamente")
            content.append({"text": f"✅ {tool_name} ejecutado exitosamente"})
            content.append({"text": raw_text})
        
        processing_time = time.time() - start_time
        
        content.append({"text": f"🆔 Request ID: {request_id}"})
        content.append({"text": f"⏱️ Tiempo: {processing_time:.2f}s"})
        
        logger.info(f"✅ Solicitud {request_id} completada en {processing_time:.2f}s")
        
        return {
            "toolResult": {
                "toolUseId": tool_id,
                "content": content
            }
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        
        logger.error(f"💥 Error en solicitud {request_id}: {error_msg}")
        logger.error(f"⏱️ Tiempo hasta error: {processing_time:.2f}s")
        
        return {
            "toolResult": {
                "toolUseId": tool_id if 'tool_id' in locals() else request_id,
                "content": [
                    {"text": f"❌ Error ejecutando {tool_name if 'tool_name' in locals() else 'unknown'}: {error_msg}"},
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
        "service": "Bedrock MCP Backend - Focused",
        "version": "2.2.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "Core MCP Tools",
            "AWS Diagrams Generation", 
            "AWS Documentation Search",
            "CloudFormation Resources",
            "Cost Calculators (Internal)",
            "Advanced File Processor",
            "S3 Auto-Upload"
        ],
        "allowed_tools": {
            "core": ["prompt_understanding"],
            "diagrams": ["generate_diagram", "list_icons", "get_diagram_examples"],
            "documentation": ["search_documentation", "read_documentation", "recommend"],
            "cloudformation": ["create_resource", "read_resource", "update_resource", "delete_resource", "list_resources", "get_resource_schema", "generate_template"],
            "pricing": ["Internal calculators via /documents/calculator/*"]
        }
    }

@app.get("/")
async def root():
    """
    🏠 Endpoint raíz con información del servicio enfocado
    """
    return {
        "service": "Bedrock MCP Backend - Focused",
        "description": "Backend enfocado para Bedrock: Core + Diagramas + Documentación + CloudFormation + Pricing",
        "version": "2.2.0",
        "focus_areas": {
            "core": "Prompt understanding y funcionalidades básicas",
            "diagrams": "Generación de diagramas AWS con iconos oficiales",
            "documentation": "Búsqueda y consulta de documentación AWS",
            "cloudformation": "Gestión de recursos y templates de infraestructura",
            "pricing": "Calculadoras de costos AWS (internas)"
        },
        "endpoints": {
            "health": "/health",
            "tool_use": "/bedrock/tool-use",
            "list_files": "/projects/{project_name}/files",
            "calculator": "/documents/calculator/generate",
            "sow": "/documents/sow/generate"
        },
        "allowed_tools_count": len(ALL_ALLOWED_TOOLS),
        "documentation": "https://bedrock-mcp.danielingram.shop"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
