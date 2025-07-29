# config.py
import os
import logging

# Configuración AWS
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "controlwebinars2025")
MCP_BASE_URL = os.getenv("MCP_BASE_URL", "https://mcp.danielingram.shop/bedrock/tool-use")  # Usar MCP externo

# Configuración de seguridad
USE_PRESIGNED_URLS = os.getenv("USE_PRESIGNED_URLS", "true").lower() == "true"
PRESIGNED_URL_EXPIRATION = int(os.getenv("PRESIGNED_URL_EXPIRATION", "3600"))  # 1 hora

# Configuración de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Map de content-types según extensión
CONTENT_TYPES = {
    "png": "image/png",
    "svg": "image/svg+xml",
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "yaml": "text/yaml",
    "yml": "text/yaml",
    "json": "application/json",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "pdf": "application/pdf",
    "md": "text/markdown"
}

class Config:
    """
    Clase de configuración para compatibilidad con file_handler
    """
    AWS_REGION = AWS_REGION
    S3_BUCKET = S3_BUCKET
    MCP_BASE_URL = MCP_BASE_URL
    USE_PRESIGNED_URLS = USE_PRESIGNED_URLS
    PRESIGNED_URL_EXPIRATION = PRESIGNED_URL_EXPIRATION

# Configuración de logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/home/ec2-user/bedrock-mcp-backend/app.log")
    ]
)

logger = logging.getLogger(__name__)
