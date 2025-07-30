#!/usr/bin/env python3
"""
Backend optimizado - Bedrock Playground con MCP inteligente
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

app = FastAPI(title="Bedrock Playground Optimized", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
class ChatRequest(BaseModel):
    message: str
    model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    temperature: float = 0.7
    max_tokens: int = 1000  # Reducido de 4000
    use_mcp: bool = True  # Control explícito
    generate_deliverables: bool = False  # Control de entregables

class ProcessStep(BaseModel):
    step: str
    status: str  # "running", "completed", "failed"
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
    error: str = None

# Cliente Bedrock
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

def should_use_mcp(message: str) -> tuple[bool, str]:
    """Decide inteligentemente cuándo usar MCP"""
    message_lower = message.lower()
    
    # Casos donde MCP es útil
    mcp_triggers = [
        "diagrama", "diagram", "arquitectura", "architecture",
        "migración", "migration", "costos", "costs", "pricing",
        "diseño", "design", "infraestructura", "infrastructure",
        "proyecto", "project", "implementar", "implement"
    ]
    
    # Casos donde Bedrock directo es mejor
    bedrock_triggers = [
        "hola", "hello", "hi", "qué tal", "como estas",
        "gracias", "thanks", "ok", "entiendo", "perfecto"
    ]
    
    for trigger in bedrock_triggers:
        if trigger in message_lower:
            return False, f"Saludo/confirmación detectado: '{trigger}'"
    
    for trigger in mcp_triggers:
        if trigger in message_lower:
            return True, f"Caso complejo detectado: '{trigger}'"
    
    # Por defecto, usar Bedrock para respuestas rápidas
    return False, "Consulta general - usando Bedrock directo"

def should_generate_deliverables(message: str) -> tuple[bool, str]:
    """Decide cuándo generar entregables (diagramas, costos, etc.)"""
    message_lower = message.lower()
    
    deliverable_triggers = [
        "diagrama", "diagram", "esquema", "blueprint",
        "costos", "costs", "pricing", "presupuesto", "budget",
        "implementar", "implement", "crear", "create",
        "proyecto completo", "full project", "entregables", "deliverables"
    ]
    
    for trigger in deliverable_triggers:
        if trigger in message_lower:
            return True, f"Solicitud de entregables detectada: '{trigger}'"
    
    return False, "No se requieren entregables"

async def call_mcp_tool_async(tool_name: str, tool_input: dict) -> dict:
    """Llama a herramienta MCP de forma asíncrona"""
    try:
        response = requests.post(
            "https://bedrock-mcp.danielingram.shop/bedrock/tool-use",
            json={
                "toolUse": {
                    "toolUseId": f"optimized-{uuid.uuid4().hex[:8]}",
                    "name": tool_name,
                    "input": tool_input
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=15  # Reducido de 30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("toolResult", {})
        else:
            return {"error": f"MCP error: {response.status_code}"}
            
    except Exception as e:
        return {"error": str(e)}

def create_optimized_prompt(message: str, context_type: str = "general") -> str:
    """Crea prompts optimizados según el contexto"""
    
    if context_type == "greeting":
        return f"""Como Arquitecto AWS experto, responde de forma concisa y profesional a: {message}

Mantén la respuesta breve (máximo 100 palabras) pero profesional."""

    elif context_type == "technical":
        return f"""Como Arquitecto de Soluciones AWS experto, proporciona una respuesta técnica y práctica para: {message}

Incluye:
- Servicios AWS específicos recomendados
- Consideraciones clave de arquitectura
- Estimación aproximada de costos si es relevante
- Próximos pasos concretos

Mantén la respuesta enfocada y práctica (máximo 300 palabras)."""

    else:
        return f"""Como Arquitecto AWS experto, responde a: {message}

Proporciona una respuesta equilibrada entre detalle técnico y claridad."""

async def process_with_bedrock_optimized(
    message: str, 
    model: str, 
    temperature: float, 
    max_tokens: int,
    context_type: str = "general"
) -> tuple[str, int, float]:
    """Procesa con Bedrock de forma optimizada"""
    
    start_time = datetime.utcnow()
    
    try:
        prompt = create_optimized_prompt(message, context_type)
        
        response = bedrock_client.converse(
            modelId=model,
            messages=[{
                "role": "user",
                "content": [{"text": prompt}]
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
    """Endpoint optimizado para chat"""
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
            deliverable_reason = "Solicitado por usuario"
        
        processing_steps.append(ProcessStep(
            step="analysis",
            status="completed",
            duration=(datetime.utcnow() - step_start).total_seconds(),
            details=f"MCP: {mcp_reason} | Entregables: {deliverable_reason}"
        ))
        
        # Paso 2: Procesamiento principal
        if use_mcp and generate_deliverables:
            # Usar MCP para generar entregables
            step_start = datetime.utcnow()
            processing_steps.append(ProcessStep(
                step="mcp_processing",
                status="running",
                details="Generando entregables con MCP..."
            ))
            
            mcp_result = await call_mcp_tool_async("prompt_understanding", {
                "query": request.message,
                "context": "AWS Solutions Architect - Generate deliverables including diagrams and cost estimates",
                "project_name": f"optimized-{request_id}"
            })
            
            if "error" not in mcp_result:
                # Procesar resultado MCP
                final_response = ""
                s3_files = []
                
                if "content" in mcp_result:
                    for item in mcp_result["content"]:
                        if "text" in item:
                            text = item["text"]
                            final_response += text + "\n"
                            
                            # Extraer URLs S3
                            urls = re.findall(r'https://[^\s]+\.s3\.amazonaws\.com/[^\s\)]+', text)
                            s3_files.extend(urls)
                
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
                    token_count=len(final_response.split())
                )
            else:
                processing_steps[-1].status = "failed"
                processing_steps[-1].details = f"MCP falló: {mcp_result['error']}"
        
        # Paso 3: Bedrock directo (optimizado)
        step_start = datetime.utcnow()
        processing_steps.append(ProcessStep(
            step="bedrock_processing",
            status="running",
            details="Procesando con Bedrock..."
        ))
        
        # Determinar contexto para optimizar prompt
        context_type = "greeting" if not use_mcp else "technical"
        
        response_text, token_count, bedrock_time = await process_with_bedrock_optimized(
            request.message,
            request.model,
            request.temperature,
            request.max_tokens,
            context_type
        )
        
        processing_steps[-1].status = "completed"
        processing_steps[-1].duration = bedrock_time
        processing_steps[-1].details = f"Bedrock completado - {token_count} tokens"
        
        # Calcular costo estimado (aproximado)
        cost_per_1k_tokens = 0.003  # Claude 3.5 Sonnet
        cost_estimate = (token_count / 1000) * cost_per_1k_tokens
        
        return ChatResponse(
            response=response_text,
            model_used=request.model,
            processing_steps=processing_steps,
            tools_used=["bedrock_optimized"],
            s3_files=[],
            request_id=request_id,
            timestamp=start_time.isoformat(),
            total_processing_time=(datetime.utcnow() - start_time).total_seconds(),
            token_count=token_count,
            cost_estimate=cost_estimate
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Bedrock Playground Optimized"}

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
                "cost_per_1k_tokens": 0.003
            },
            {
                "id": "amazon.nova-pro-v1:0", 
                "name": "Amazon Nova Pro v1",
                "provider": "Amazon",
                "type": "on-demand",
                "max_tokens": 4096,
                "cost_per_1k_tokens": 0.0008
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
