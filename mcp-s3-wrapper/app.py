# MCP S3 Wrapper - Proxy que agrega subida automática a S3
from fastapi import FastAPI, Request
import requests
import boto3
import json
import uuid
import logging
from datetime import datetime
import os

# Configuración
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "controlwebinars2025")
ORIGINAL_MCP_URL = os.getenv("ORIGINAL_MCP_URL", "https://mcp.danielingram.shop/bedrock/tool-use")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS S3 client
s3 = boto3.client("s3", region_name=AWS_REGION)

app = FastAPI(title="MCP S3 Wrapper", version="1.0.0")

def upload_to_s3(content: bytes, filename: str, project_name: str = "general", tool_name: str = "misc") -> str:
    """Sube archivo a S3 y devuelve URL"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        key = f"arquitecturas/{project_name}/{tool_name}/{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
        
        # Determinar content type
        content_type = "image/png" if filename.endswith('.png') else "application/octet-stream"
        
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata={
                "project": project_name,
                "tool": tool_name,
                "timestamp": timestamp
            }
        )
        
        # Generar URL presignada (válida por 1 hora)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=3600
        )
        
        logger.info(f"✅ Archivo subido a S3: {key}")
        return url
        
    except Exception as e:
        logger.error(f"❌ Error subiendo a S3: {str(e)}")
        raise

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mcp-s3-wrapper"}

@app.post("/bedrock/tool-use")
async def proxy_with_s3(request: Request):
    """
    Proxy que intercepta generate_diagram y agrega subida automática a S3
    """
    body = await request.json()
    tool_use = body.get("toolUse", {})
    tool_name = tool_use.get("name")
    
    logger.info(f"🔧 Procesando herramienta: {tool_name}")
    
    try:
        # 1️⃣ Llamar al MCP original
        response = requests.post(ORIGINAL_MCP_URL, json=body, timeout=180)
        
        if response.status_code != 200:
            return {"error": f"MCP error: {response.status_code}"}
        
        result = response.json()
        
        # 2️⃣ Si es generate_diagram, interceptar y subir a S3
        if tool_name == "generate_diagram":
            tool_result = result.get("toolResult", {})
            content = tool_result.get("content", [])
            
            for item in content:
                if "text" in item:
                    try:
                        # Parsear respuesta JSON del MCP
                        mcp_data = json.loads(item["text"])
                        
                        if mcp_data.get("status") == "success" and "path" in mcp_data:
                            local_path = mcp_data["path"]
                            filename = local_path.split("/")[-1]
                            
                            logger.info(f"📁 Interceptando archivo: {filename}")
                            
                            # 3️⃣ Intentar descargar el archivo del MCP
                            file_url = f"https://mcp.danielingram.shop/files{local_path}"
                            file_response = requests.get(file_url, timeout=30)
                            
                            if file_response.status_code == 200:
                                # 4️⃣ Subir a S3
                                project_name = tool_use.get("input", {}).get("project_name", "auto-generated")
                                s3_url = upload_to_s3(
                                    file_response.content, 
                                    filename, 
                                    project_name, 
                                    tool_name
                                )
                                
                                # 5️⃣ Modificar respuesta para incluir S3 URL
                                mcp_data["s3_url"] = s3_url
                                mcp_data["message"] = f"Diagram generated and uploaded to S3: {s3_url}"
                                
                                # Actualizar el contenido
                                item["text"] = json.dumps(mcp_data, indent=2)
                                
                                logger.info(f"✅ Archivo subido y respuesta modificada")
                            else:
                                logger.warning(f"⚠️ No se pudo descargar archivo del MCP: {file_response.status_code}")
                                
                    except json.JSONDecodeError:
                        # No es JSON, pasar tal como está
                        continue
                    except Exception as e:
                        logger.error(f"❌ Error procesando archivo: {str(e)}")
                        continue
        
        return result
        
    except Exception as e:
        logger.error(f"💥 Error en proxy: {str(e)}")
        return {
            "toolResult": {
                "toolUseId": tool_use.get("toolUseId", "unknown"),
                "content": [
                    {"text": f"❌ Error en MCP S3 Wrapper: {str(e)}"}
                ]
            }
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Iniciando MCP S3 Wrapper")
    uvicorn.run(app, host="0.0.0.0", port=8001)
