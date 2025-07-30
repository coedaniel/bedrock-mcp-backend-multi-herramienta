#!/usr/bin/env python3
"""
Backend optimizado con System Prompt - Bedrock Playground con MCP
Puerto 8001 (reemplazando versión anterior)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import boto3
import logging
import traceback
from datetime import datetime
import uuid
import requests
import re
import asyncio

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bedrock Playground with System Prompt", version="2.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System Prompt para Arquitecto AWS
AWS_ARCHITECT_SYSTEM_PROMPT = """Eres un Arquitecto de Soluciones AWS Senior con más de 10 años de experiencia en diseño de arquitecturas empresariales en la nube.

🎯 TU IDENTIDAD:
- Arquitecto de Soluciones AWS certificado (Solutions Architect Professional)
- Experto en migración, modernización y optimización de cargas de trabajo
- Especialista en Well-Architected Framework y mejores prácticas de AWS

📋 TUS RESPONSABILIDADES:
- Diseñar arquitecturas escalables, seguras y rentables
- Proporcionar recomendaciones específicas de servicios AWS
- Estimar costos aproximados cuando sea relevante
- Sugerir mejores prácticas de seguridad y compliance
- Ofrecer pasos concretos de implementación

🎨 TU ESTILO DE COMUNICACIÓN:
- Profesional pero accesible
- Respuestas estructuradas con bullets y numeración
- Incluye consideraciones técnicas y de negocio
- Menciona servicios AWS específicos con sus beneficios
- Proporciona estimaciones realistas de tiempo y costo

🚫 RESTRICCIONES:
- No inventes precios exactos (usa rangos aproximados)
- No hagas suposiciones sobre compliance específico sin preguntar
- Siempre considera el principio de menor privilegio en seguridad
- Recomienda soluciones que sigan el Well-Architected Framework

🛠️ CUANDO GENERAR ENTREGABLES:
- Si mencionan "diagrama", "arquitectura visual", "esquema"
- Si piden "costos detallados", "presupuesto", "estimación"
- Si dicen "proyecto completo", "implementación", "entregables"
- Si solicitan "documentación", "plan de migración"

Responde siempre como este Arquitecto AWS experto, manteniendo consistencia en tu identidad y estilo."""

# Modelos
class ChatRequest(BaseModel):
    message: str
    model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    temperature: float = 0.7
    max_tokens: int = 1000
    use_mcp: bool = True
    generate_deliverables: bool = False
    system_prompt: str = AWS_ARCHITECT_SYSTEM_PROMPT

class ProcessStep(BaseModel):
    step: str
    status: str
    duration: float = 0
    details: str = ""

class ChatResponse(BaseModel):
    response: str
    model_used: str
    processing_steps: list[ProcessStep] = []
    tools_used: list = []
    s3_files: list = []
    request_id: str
    timestamp: str
    total_processing_time: float
    token_count: int = 0
    cost_estimate: float = 0.0
    system_prompt_used: bool = True
    error: str = None

# Cliente Bedrock
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

def should_use_mcp(message: str) -> tuple[bool, str]:
    """Decide inteligentemente cuándo usar MCP"""
    message_lower = message.lower()
    
    # Casos donde MCP es útil (entregables)
    mcp_triggers = [
        "diagrama", "diagram", "arquitectura visual", "esquema", "blueprint",
        "costos detallados", "costs", "pricing", "presupuesto", "budget",
        "proyecto completo", "implementación", "entregables", "deliverables",
        "documentación", "plan de migración", "migration plan"
    ]
    
    # Casos donde Bedrock directo es mejor
    bedrock_triggers = [
        "hola", "hello", "hi", "qué tal", "como estas",
        "gracias", "thanks", "ok", "entiendo", "perfecto",
        "explica", "explain", "qué es", "what is", "cómo funciona"
    ]
    
    for trigger in bedrock_triggers:
        if trigger in message_lower:
            return False, f"Consulta conversacional: '{trigger}'"
    
    for trigger in mcp_triggers:
        if trigger in message_lower:
            return True, f"Entregables solicitados: '{trigger}'"
    
    # Para consultas técnicas, usar Bedrock directo (más rápido)
    return False, "Consulta técnica - Bedrock directo"

def should_generate_deliverables(message: str) -> tuple[bool, str]:
    """Decide cuándo generar entregables específicos"""
    message_lower = message.lower()
    
    deliverable_triggers = [
        "diagrama", "diagram", "esquema", "blueprint", "visual",
        "costos detallados", "detailed costs", "presupuesto completo",
        "proyecto completo", "full project", "implementación completa",
        "entregables", "deliverables", "documentos", "documents"
    ]
    
    for trigger in deliverable_triggers:
        if trigger in message_lower:
            return True, f"Entregables específicos: '{trigger}'"
    
    return False, "Solo consulta - sin entregables"

async def call_mcp_tool_async(tool_name: str, tool_input: dict) -> dict:
    """Llama a herramienta MCP de forma asíncrona"""
    try:
        response = requests.post(
            "https://bedrock-mcp.danielingram.shop/bedrock/tool-use",
            json={
                "toolUse": {
                    "toolUseId": f"system-prompt-{uuid.uuid4().hex[:8]}",
                    "name": tool_name,
                    "input": tool_input
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("toolResult", {})
        else:
            return {"error": f"MCP error: {response.status_code}"}
            
    except Exception as e:
        return {"error": str(e)}

async def process_with_bedrock_system_prompt(
    message: str, 
    model: str, 
    temperature: float, 
    max_tokens: int,
    system_prompt: str
) -> tuple[str, int, float]:
    """Procesa con Bedrock usando System Prompt (como Bedrock Playground)"""
    
    start_time = datetime.utcnow()
    
    try:
        # Usar system prompt + mensaje del usuario (como Bedrock Playground)
        response = bedrock_client.converse(
            modelId=model,
            messages=[{
                "role": "user",
                "content": [{"text": message}]
            }],
            system=[{
                "text": system_prompt
            }],
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature
            }
        )
        
        text_response = ""
        token_count = 0
        
        if "output" in response and "message" in response["output"]:
            for content in response["output"]["message"]["content"]:
                if "text" in content:
                    text_response += content["text"]
        
        if "usage" in response:
            token_count = response["usage"].get("outputTokens", 0)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return text_response, token_count, processing_time
        
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        raise Exception(f"Bedrock error: {str(e)}")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Endpoint optimizado con System Prompt"""
    try:
        request_id = uuid.uuid4().hex[:8]
        start_time = datetime.utcnow()
        processing_steps = []
        
        logger.info(f"Chat request: {request.message[:50]}...")
        
        # Paso 1: Análisis de la consulta
        step_start = datetime.utcnow()
        use_mcp, mcp_reason = should_use_mcp(request.message)
        generate_deliverables, deliverable_reason = should_generate_deliverables(request.message)
        
        # Override manual
        if not request.use_mcp:
            use_mcp = False
            mcp_reason = "Deshabilitado por usuario"
        
        if request.generate_deliverables:
            generate_deliverables = True
            deliverable_reason = "Forzado por usuario"
        
        processing_steps.append(ProcessStep(
            step="analysis",
            status="completed",
            duration=(datetime.utcnow() - step_start).total_seconds(),
            details=f"MCP: {mcp_reason} | Entregables: {deliverable_reason}"
        ))
        
        # Paso 2: Procesamiento con MCP (si es necesario)
        if use_mcp and generate_deliverables:
            step_start = datetime.utcnow()
            processing_steps.append(ProcessStep(
                step="mcp_processing",
                status="running",
                details="Generando entregables con MCP..."
            ))
            
            mcp_result = await call_mcp_tool_async("prompt_understanding", {
                "query": request.message,
                "context": "AWS Solutions Architect - Generate comprehensive deliverables including diagrams and detailed cost estimates",
                "project_name": f"system-prompt-{request_id}"
            })
            
            if "error" not in mcp_result and "content" in mcp_result:
                # Verificar si MCP generó contenido útil
                final_response = ""
                s3_files = []
                
                for item in mcp_result["content"]:
                    if "text" in item:
                        text = item["text"]
                        
                        # Si no es solo metadata, usar MCP
                        if not ("prompt_understanding ejecutado exitosamente" in text and len(text.split('\n')) < 10):
                            final_response += text + "\n"
                        
                        # Extraer URLs S3
                        urls = re.findall(r'https://[^\s]+\.s3\.amazonaws\.com/[^\s\)]+', text)
                        s3_files.extend(urls)
                
                if final_response.strip() and len(final_response.strip()) > 100:
                    processing_steps[-1].status = "completed"
                    processing_steps[-1].duration = (datetime.utcnow() - step_start).total_seconds()
                    processing_steps[-1].details = f"MCP completado - {len(s3_files)} archivos generados"
                    
                    return ChatResponse(
                        response=final_response.strip(),
                        model_used=request.model,
                        processing_steps=processing_steps,
                        tools_used=["prompt_understanding"],
                        s3_files=s3_files,
                        request_id=request_id,
                        timestamp=start_time.isoformat(),
                        total_processing_time=(datetime.utcnow() - start_time).total_seconds(),
                        token_count=len(final_response.split()),
                        system_prompt_used=False  # MCP no usa system prompt
                    )
            
            # Si MCP falla o devuelve solo metadata
            processing_steps[-1].status = "failed"
            processing_steps[-1].details = "MCP devolvió solo metadata - usando Bedrock"
        
        # Paso 3: Bedrock con System Prompt (comportamiento por defecto)
        step_start = datetime.utcnow()
        processing_steps.append(ProcessStep(
            step="bedrock_processing",
            status="running",
            details="Procesando con System Prompt..."
        ))
        
        response_text, token_count, bedrock_time = await process_with_bedrock_system_prompt(
            request.message,
            request.model,
            request.temperature,
            request.max_tokens,
            request.system_prompt
        )
        
        processing_steps[-1].status = "completed"
        processing_steps[-1].duration = bedrock_time
        processing_steps[-1].details = f"Bedrock + System Prompt - {token_count} tokens"
        
        # Calcular costo estimado
        cost_per_1k_tokens = 0.003 if "claude" in request.model else 0.0008
        cost_estimate = (token_count / 1000) * cost_per_1k_tokens
        
        return ChatResponse(
            response=response_text,
            model_used=request.model,
            processing_steps=processing_steps,
            tools_used=["bedrock_system_prompt"],
            s3_files=[],
            request_id=request_id,
            timestamp=start_time.isoformat(),
            total_processing_time=(datetime.utcnow() - start_time).total_seconds(),
            token_count=token_count,
            cost_estimate=cost_estimate,
            system_prompt_used=True
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Bedrock Playground with System Prompt"}

@app.get("/system-prompt")
async def get_system_prompt():
    """Endpoint para obtener el System Prompt actual"""
    return {
        "system_prompt": AWS_ARCHITECT_SYSTEM_PROMPT,
        "description": "System Prompt para Arquitecto AWS Senior",
        "version": "2.1.0"
    }

@app.post("/system-prompt")
async def update_system_prompt(new_prompt: dict):
    """Endpoint para actualizar el System Prompt"""
    global AWS_ARCHITECT_SYSTEM_PROMPT
    if "prompt" in new_prompt:
        AWS_ARCHITECT_SYSTEM_PROMPT = new_prompt["prompt"]
        return {"status": "updated", "message": "System Prompt actualizado"}
    else:
        raise HTTPException(status_code=400, detail="Campo 'prompt' requerido")

@app.get("/models")
async def get_models():
    return {
        "models": [
            {
                "id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "name": "Claude 3.5 Sonnet v1",
                "provider": "Anthropic",
                "type": "on-demand",
                "max_tokens": 8192,
                "cost_per_1k_tokens": 0.003,
                "supports_system_prompt": True
            },
            {
                "id": "amazon.nova-pro-v1:0", 
                "name": "Amazon Nova Pro v1",
                "provider": "Amazon",
                "type": "on-demand",
                "max_tokens": 4096,
                "cost_per_1k_tokens": 0.0008,
                "supports_system_prompt": True
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
