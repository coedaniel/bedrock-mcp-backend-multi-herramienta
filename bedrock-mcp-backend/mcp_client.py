# mcp_client.py
import requests
import json
import logging
from config import MCP_BASE_URL

logger = logging.getLogger(__name__)

def call_mcp_tool(tool_name: str, arguments: dict, conversation_id: str = None, message_id: str = None) -> dict:
    """
    Llama a cualquier herramienta MCP con logging detallado.
    """
    logger.info(f"🔧 Iniciando llamada MCP: {tool_name}")
    logger.debug(f"📝 Argumentos: {json.dumps(arguments, indent=2)}")
    
    # Estructura del payload según el formato observado
    payload = {
        "toolUse": {
            "toolUseId": f"bedrock-{tool_name}-{message_id or 'auto'}",
            "name": tool_name,
            "input": arguments
        },
        "conversationId": conversation_id or f"bedrock-conversation-{tool_name}",
        "messageId": message_id or f"bedrock-message-{tool_name}"
    }
    
    logger.debug(f"📤 Payload MCP: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(MCP_BASE_URL, json=payload, timeout=180)
        logger.info(f"📡 Respuesta MCP status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ Error MCP {response.status_code}: {response.text}")
            raise Exception(f"MCP error {response.status_code}: {response.text}")
        
        response_data = response.json()
        logger.info(f"📥 Respuesta MCP completa: {json.dumps(response_data, indent=2)}")
        
        # Extraer el resultado del toolResult
        tool_result = response_data.get("toolResult", {})
        content = tool_result.get("content", [])
        logger.info(f"📋 Content extraído: {json.dumps(content, indent=2)}")
        
        # Buscar contenido de texto que pueda contener JSON
        result_data = {}
        for item in content:
            if item.get("type") == "text":
                text_content = item.get("text", "")
                try:
                    # Intentar parsear como JSON si es posible
                    parsed_content = json.loads(text_content)
                    result_data.update(parsed_content)
                    logger.info(f"✅ Contenido JSON parseado exitosamente")
                except json.JSONDecodeError:
                    # Si no es JSON, guardarlo como texto plano
                    result_data["raw_text"] = text_content
                    logger.info(f"📄 Contenido guardado como texto plano")
            elif "text" in item:
                # Manejar items sin type pero con text
                text_content = item.get("text", "")
                try:
                    parsed_content = json.loads(text_content)
                    result_data.update(parsed_content)
                    logger.info(f"✅ Contenido JSON parseado exitosamente (sin type)")
                except json.JSONDecodeError:
                    if "raw_text" not in result_data:
                        result_data["raw_text"] = text_content
                    else:
                        result_data["raw_text"] += "\n" + text_content
                    logger.info(f"📄 Contenido agregado como texto plano")
        
        logger.info(f"✅ MCP {tool_name} completado exitosamente")
        return {"result": result_data}
        
    except requests.exceptions.Timeout:
        logger.error(f"⏰ Timeout en MCP {tool_name}")
        raise Exception(f"Timeout calling MCP tool {tool_name}")
    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Error de conexión MCP {tool_name}: {str(e)}")
        raise Exception(f"Connection error calling MCP tool {tool_name}: {str(e)}")
    except Exception as e:
        logger.error(f"💥 Error inesperado MCP {tool_name}: {str(e)}")
        raise
