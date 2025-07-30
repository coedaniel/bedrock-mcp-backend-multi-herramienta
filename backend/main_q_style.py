from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
import json
import time
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import re
import logging
from s3_uploader import S3FileUploader
from security_enhancements import security_manager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar S3 Uploader
s3_uploader = S3FileUploader()

app = FastAPI(title="Bedrock Chat API - Amazon Q Style", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente Bedrock
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# System Prompt por defecto (editable como Bedrock Playground)
DEFAULT_SYSTEM_PROMPT = """Eres un Arquitecto de Soluciones AWS experto que trabaja como Amazon Q CLI. Tu comportamiento debe ser:

## IDENTIDAD
- Nombre: Amazon Q para AWS
- Rol: Arquitecto de Soluciones AWS Senior
- Especialidad: Diseño de arquitecturas cloud, optimización de costos, mejores prácticas

## COMPORTAMIENTO CONVERSACIONAL (Como Amazon Q CLI)
- SIEMPRE haz preguntas específicas antes de generar entregables complejos
- Para solicitudes como "necesito costos" o "crea un diagrama", pregunta PRIMERO:
  * ¿Qué servicios específicos necesitas?
  * ¿Cuál es tu presupuesto estimado?
  * ¿Qué región prefieres?
  * ¿Tienes requisitos de compliance?
- Solo genera entregables después de tener contexto suficiente
- Sé conversacional y educativo, no solo transaccional

## RESPONSABILIDADES
1. **Arquitectura**: Diseñar soluciones escalables y seguras
2. **Costos**: Optimizar gastos y proporcionar estimaciones precisas
3. **Mejores Prácticas**: Aplicar Well-Architected Framework
4. **Educación**: Explicar decisiones técnicas claramente

## ESTILO DE COMUNICACIÓN
- Profesional pero accesible
- Usa ejemplos prácticos
- Incluye consideraciones de seguridad
- Menciona alternativas cuando sea relevante
- Pregunta antes de asumir requisitos

## RESTRICCIONES
- No generes código malicioso
- No hagas suposiciones sobre datos sensibles
- Siempre considera seguridad y compliance
- Pregunta por detalles antes de crear entregables complejos

Recuerda: Como Amazon Q CLI, tu objetivo es ser útil a través de conversación inteligente, no solo generar respuestas automáticas."""

# Variable global para el system prompt actual
current_system_prompt = DEFAULT_SYSTEM_PROMPT

# Modelos de datos
class ChatRequest(BaseModel):
    message: str
    model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    temperature: float = 0.7
    max_tokens: int = 1500
    use_mcp: bool = True
    generate_deliverables: bool = False
    system_prompt: Optional[str] = None

class SystemPromptRequest(BaseModel):
    prompt: str

class ProcessingStep:
    def __init__(self, step: str, details: str, status: str = "running"):
        self.step = step
        self.details = details
        self.status = status
        self.start_time = time.time()
        self.duration = 0
        self.mcp_tool = None
        self.reasoning = None
    
    def complete(self, details: str = None):
        self.status = "completed"
        self.duration = time.time() - self.start_time
        if details:
            self.details = details
    
    def fail(self, details: str = None):
        self.status = "failed"
        self.duration = time.time() - self.start_time
        if details:
            self.details = details

# Funciones de análisis
def analyze_intent(message: str) -> Dict[str, Any]:
    """Analiza la intención del mensaje para determinar si necesita MCP"""
    
    # Palabras clave que indican necesidad de entregables
    deliverable_keywords = [
        'diagrama', 'diagram', 'arquitectura', 'architecture',
        'costo', 'cost', 'precio', 'pricing', 'presupuesto', 'budget',
        'documentación', 'documentation', 'doc',
        'generar', 'generate', 'crear', 'create', 'diseñar', 'design',
        'migración', 'migration', 'implementar', 'implement'
    ]
    
    # Palabras clave que indican preguntas simples
    simple_keywords = [
        'qué es', 'what is', 'cómo', 'how', 'por qué', 'why',
        'explica', 'explain', 'diferencia', 'difference',
        'ventajas', 'advantages', 'desventajas', 'disadvantages'
    ]
    
    message_lower = message.lower()
    
    # Contar coincidencias
    deliverable_matches = sum(1 for keyword in deliverable_keywords if keyword in message_lower)
    simple_matches = sum(1 for keyword in simple_keywords if keyword in message_lower)
    
    # Determinar intención
    if deliverable_matches > simple_matches and deliverable_matches > 0:
        intent = "deliverable_request"
        confidence = min(0.9, 0.5 + (deliverable_matches * 0.1))
    elif simple_matches > 0:
        intent = "information_request"
        confidence = min(0.9, 0.6 + (simple_matches * 0.1))
    else:
        intent = "general_conversation"
        confidence = 0.5
    
    return {
        "intent": intent,
        "confidence": confidence,
        "deliverable_matches": deliverable_matches,
        "simple_matches": simple_matches,
        "reasoning": f"Detectadas {deliverable_matches} palabras de entregables, {simple_matches} de información simple"
    }

async def call_mcp_tool(message: str, step: ProcessingStep) -> Dict[str, Any]:
    """Llama al backend MCP para procesamiento avanzado"""
    
    step.mcp_tool = "prompt_understanding"
    step.reasoning = "Usando MCP para análisis completo y generación de entregables"
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "tools": [
                    {
                        "name": "awslabscore_mcp_server___prompt_understanding",
                        "arguments": {}
                    }
                ]
            }
            
            async with session.post(
                "https://bedrock-mcp.danielingram.shop/bedrock/tool-use",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Extraer contenido de la respuesta MCP
                    content = ""
                    s3_files = []
                    
                    if "content" in result and isinstance(result["content"], list):
                        for item in result["content"]:
                            if item.get("type") == "text":
                                content += item.get("text", "")
                            elif item.get("type") == "resource":
                                # Extraer URLs de S3 del contenido
                                resource_text = item.get("resource", {}).get("text", "")
                                s3_urls = re.findall(r'https://[^\s]+\.s3[^\s]*', resource_text)
                                s3_files.extend(s3_urls)
                    
                    return {
                        "success": True,
                        "content": content or "Procesamiento MCP completado",
                        "s3_files": s3_files,
                        "raw_response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"MCP HTTP {response.status}",
                        "content": "Error en procesamiento MCP"
                    }
                    
    except Exception as e:
        logger.error(f"Error calling MCP: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": "Error de conexión con MCP"
        }

async def call_bedrock_with_system_prompt(message: str, model: str, temperature: float, max_tokens: int, system_prompt: str, step: ProcessingStep) -> Dict[str, Any]:
    """Llama a Bedrock con System Prompt personalizado"""
    
    step.reasoning = "Usando Bedrock con System Prompt personalizado para respuesta directa"
    
    try:
        # Preparar el cuerpo de la solicitud según el modelo
        if "claude" in model:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            }
        elif "nova" in model:
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": f"{system_prompt}\n\nUsuario: {message}"}]
                    }
                ],
                "inferenceConfig": {
                    "temperature": temperature,
                    "maxTokens": max_tokens
                }
            }
        else:
            raise ValueError(f"Modelo no soportado: {model}")
        
        # Llamar a Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=model,
            body=json.dumps(body),
            contentType="application/json"
        )
        
        # Procesar respuesta
        response_body = json.loads(response['body'].read())
        
        if "claude" in model:
            content = response_body['content'][0]['text']
            input_tokens = response_body.get('usage', {}).get('input_tokens', 0)
            output_tokens = response_body.get('usage', {}).get('output_tokens', 0)
        elif "nova" in model:
            content = response_body['output']['message']['content'][0]['text']
            input_tokens = response_body.get('usage', {}).get('inputTokens', 0)
            output_tokens = response_body.get('usage', {}).get('outputTokens', 0)
        
        total_tokens = input_tokens + output_tokens
        
        # Calcular costo estimado (precios aproximados)
        if "claude-3-5-sonnet" in model:
            cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000
        elif "nova-pro" in model:
            cost = (input_tokens * 0.0008 + output_tokens * 0.0032) / 1000
        else:
            cost = 0.001  # Estimación genérica
        
        return {
            "success": True,
            "content": content,
            "token_count": total_tokens,
            "cost_estimate": cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }
        
    except Exception as e:
        logger.error(f"Error calling Bedrock: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": f"Error en Bedrock: {str(e)}",
            "token_count": 0,
            "cost_estimate": 0
        }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, http_request: Request):
    """Endpoint principal de chat con flujo inteligente estilo Amazon Q CLI + Seguridad"""
    
    # Obtener IP del cliente
    client_ip = http_request.client.host
    
    # Validación de seguridad
    security_result = security_manager.validate_request(
        request.dict(), 
        client_ip
    )
    
    if not security_result["valid"]:
        logger.warning(f"Security validation failed for IP {client_ip}: {security_result['errors']}")
        raise HTTPException(
            status_code=429 if "Rate limit" in str(security_result["errors"]) else 400,
            detail=security_result["errors"]
        )
    
    # Log warnings si existen
    if security_result["warnings"]:
        logger.warning(f"Security warnings for IP {client_ip}: {security_result['warnings']}")
    
    # Usar datos sanitizados
    sanitized_data = security_result.get("sanitized_data", request.dict())
    sanitized_request = ChatRequest(**sanitized_data)
    
    start_time = time.time()
    processing_steps = []
    
    # Usar system prompt del request o el actual
    system_prompt = sanitized_request.system_prompt or current_system_prompt
    
    # Paso 1: Análisis de intención
    step1 = ProcessingStep("intent_analysis", "Analizando intención del mensaje...")
    processing_steps.append(step1)
    
    intent_analysis = analyze_intent(sanitized_request.message)
    step1.complete(f"Intención: {intent_analysis['intent']} (confianza: {intent_analysis['confidence']:.2f})")
    step1.reasoning = intent_analysis['reasoning']
    
    # Paso 2: Decisión de procesamiento
    step2 = ProcessingStep("context_gathering", "Determinando estrategia de respuesta...")
    processing_steps.append(step2)
    
    use_mcp = False
    conversation_stage = "response"
    
    if request.generate_deliverables:
        # Forzar uso de MCP
        use_mcp = True
        conversation_stage = "deliverable_generation"
        step2.complete("Forzando generación de entregables via MCP")
    elif request.use_mcp and intent_analysis["intent"] == "deliverable_request":
        # Usar MCP para solicitudes de entregables
        use_mcp = True
        conversation_stage = "clarification_needed"
        step2.complete("Usando MCP para solicitud de entregables")
    else:
        # Usar Bedrock directo con System Prompt
        use_mcp = False
        conversation_stage = "direct_response"
        step2.complete("Usando Bedrock directo con System Prompt")
    
    # Paso 3: Procesamiento
    if use_mcp:
        step3 = ProcessingStep("mcp_processing", "Procesando con MCP backend...")
        processing_steps.append(step3)
        
        mcp_result = await call_mcp_tool(request.message, step3)
        
        if mcp_result["success"]:
            step3.complete("MCP procesado exitosamente")
            
            # Procesar archivos generados y subirlos a S3
            s3_files = []
            if "files_generated" in mcp_result:
                for file_info in mcp_result["files_generated"]:
                    try:
                        s3_url = s3_uploader.upload_file_content(
                            file_info["content"],
                            file_info["type"],
                            file_info.get("filename")
                        )
                        s3_files.append({
                            "filename": file_info.get("filename", "generated_file"),
                            "type": file_info["type"],
                            "s3_url": s3_url
                        })
                    except Exception as e:
                        logger.error(f"Error uploading file to S3: {str(e)}")
            
            response_data = {
                "response": mcp_result["content"],
                "processing_steps": [
                    {
                        "step": step.step,
                        "details": step.details,
                        "status": step.status,
                        "duration": step.duration,
                        "mcp_tool": getattr(step, 'mcp_tool', None),
                        "reasoning": getattr(step, 'reasoning', None)
                    }
                    for step in processing_steps
                ],
                "total_processing_time": time.time() - start_time,
                "token_count": len(mcp_result["content"].split()) * 1.3,  # Estimación
                "cost_estimate": 0.002,  # Estimación para MCP
                "tools_used": ["MCP", "prompt_understanding"],
                "s3_files": s3_files,
                "conversation_stage": conversation_stage,
                "system_prompt_used": False
            }
            
            return response_data
        else:
            step3.fail(f"Error MCP: {mcp_result['error']}")
            # Fallback a Bedrock
            step4 = ProcessingStep("bedrock_processing", "Fallback a Bedrock con System Prompt...")
            processing_steps.append(step4)
    else:
        step3 = ProcessingStep("bedrock_processing", "Procesando con Bedrock + System Prompt...")
        processing_steps.append(step3)
        step4 = step3
    
    # Procesamiento con Bedrock
    bedrock_result = await call_bedrock_with_system_prompt(
        request.message, request.model, request.temperature, 
        request.max_tokens, system_prompt, step4
    )
    
    if bedrock_result["success"]:
        step4.complete("Bedrock procesado exitosamente")
        
        response_data = {
            "response": bedrock_result["content"],
            "processing_steps": [
                {
                    "step": step.step,
                    "details": step.details,
                    "status": step.status,
                    "duration": step.duration,
                    "mcp_tool": getattr(step, 'mcp_tool', None),
                    "reasoning": getattr(step, 'reasoning', None)
                }
                for step in processing_steps
            ],
            "total_processing_time": time.time() - start_time,
            "token_count": bedrock_result["token_count"],
            "cost_estimate": bedrock_result["cost_estimate"],
            "tools_used": ["Bedrock", request.model.split('.')[-1]],
            "s3_files": [],
            "conversation_stage": conversation_stage,
            "system_prompt_used": True
        }
        
        return response_data
    else:
        step4.fail(f"Error Bedrock: {bedrock_result['error']}")
        raise HTTPException(status_code=500, detail=bedrock_result["error"])

@app.get("/system-prompt")
async def get_system_prompt():
    """Obtener el System Prompt actual"""
    return {"system_prompt": current_system_prompt}

@app.post("/system-prompt")
async def update_system_prompt(request: SystemPromptRequest):
    """Actualizar el System Prompt"""
    global current_system_prompt
    current_system_prompt = request.prompt
    return {"message": "System Prompt actualizado exitosamente", "system_prompt": current_system_prompt}

@app.post("/system-prompt/reset")
async def reset_system_prompt():
    """Resetear el System Prompt al valor por defecto"""
    global current_system_prompt
    current_system_prompt = DEFAULT_SYSTEM_PROMPT
    return {"message": "System Prompt reseteado al valor por defecto", "system_prompt": current_system_prompt}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "features": [
            "Amazon Q Style Conversation",
            "Editable System Prompt",
            "S3 File Upload",
            "MCP Integration",
            "Processing Steps"
        ]
    }

# NUEVOS ENDPOINTS PARA S3
@app.post("/upload-file")
async def upload_file_to_s3(request: dict):
    """Subir archivo a S3"""
    try:
        content = request.get('content', '')
        file_type = request.get('file_type', 'text')
        filename = request.get('filename')
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        s3_url = s3_uploader.upload_file_content(content, file_type, filename)
        
        return {
            "success": True,
            "s3_url": s3_url,
            "message": "File uploaded successfully"
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-json")
async def upload_json_to_s3(request: dict):
    """Subir datos JSON a S3"""
    try:
        data = request.get('data', {})
        filename = request.get('filename')
        
        if not data:
            raise HTTPException(status_code=400, detail="Data is required")
        
        s3_url = s3_uploader.upload_json_data(data, filename)
        
        return {
            "success": True,
            "s3_url": s3_url,
            "message": "JSON data uploaded successfully"
        }
    
    except Exception as e:
        logger.error(f"Error uploading JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-files")
async def list_s3_files(file_type: Optional[str] = None, limit: int = 50):
    """Listar archivos subidos a S3"""
    try:
        files = s3_uploader.list_uploaded_files(file_type, limit)
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/security-status")
async def get_security_status():
    """Obtener estado de seguridad"""
    try:
        audit_logs = security_manager.audit_logger.get_recent_logs(24)
        
        # Estadísticas básicas
        total_requests = len(audit_logs)
        failed_validations = len([log for log in audit_logs if not log.get('validation_passed', True)])
        warnings = len([log for log in audit_logs if log.get('warnings')])
        
        return {
            "status": "active",
            "last_24_hours": {
                "total_requests": total_requests,
                "failed_validations": failed_validations,
                "warnings": warnings,
                "success_rate": (total_requests - failed_validations) / max(total_requests, 1) * 100
            },
            "rate_limiting": {
                "enabled": True,
                "max_requests_per_minute": 10
            },
            "input_validation": {
                "enabled": True,
                "max_message_length": 10000
            },
            "anomaly_detection": {
                "enabled": True,
                "suspicious_keywords_count": len(security_manager.anomaly_detector.suspicious_keywords)
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting security status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rate-limit-status/{client_ip}")
async def get_rate_limit_status(client_ip: str):
    """Verificar estado de rate limiting para una IP"""
    try:
        remaining = security_manager.rate_limiter.get_remaining_requests(client_ip)
        return {
            "client_ip": client_ip,
            "remaining_requests": remaining,
            "max_requests": security_manager.rate_limiter.max_requests,
            "window_minutes": security_manager.rate_limiter.window_seconds / 60
        }
    
    except Exception as e:
        logger.error(f"Error getting rate limit status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete-file")
async def delete_s3_file(s3_url: str):
    """Eliminar archivo de S3"""
    try:
        success = s3_uploader.delete_file(s3_url)
        
        if success:
            return {
                "success": True,
                "message": "File deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
    uvicorn.run(app, host="0.0.0.0", port=8001)
