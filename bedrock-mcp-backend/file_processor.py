"""
🔧 Procesador de archivos avanzado para MCP + S3
Detecta automáticamente archivos generados por MCP y los sube a S3
"""

import re
import base64
import binascii
import json
import uuid
import logging
from typing import Dict, List, Tuple, Optional
from s3_utils import upload_to_s3, generate_presigned_url
from config import USE_PRESIGNED_URLS

logger = logging.getLogger(__name__)

class FileProcessor:
    """Procesador inteligente de archivos MCP"""
    
    # Patrones para detectar diferentes tipos de archivos
    FILE_PATTERNS = {
        'png': [
            r'data:image/png;base64,([A-Za-z0-9+/=]+)',
            r'iVBORw0KGgo[A-Za-z0-9+/=]+',  # PNG header en base64
            r'89504e47[0-9a-fA-F]+',  # PNG header en hex
        ],
        'svg': [
            r'<svg[^>]*>.*?</svg>',
            r'data:image/svg\+xml[^"\']*',
        ],
        'csv': [
            r'([^,\n]+,){2,}[^,\n]*\n',  # CSV pattern
            r'data:text/csv[^"\']*',
        ],
        'xlsx': [
            r'data:application/vnd\.openxmlformats[^"\']*',
            r'UEsDBBQA[A-Za-z0-9+/=]+',  # XLSX header en base64
        ],
        'docx': [
            r'data:application/vnd\.openxmlformats-officedocument\.wordprocessingml[^"\']*',
            r'UEsDBBQA[A-Za-z0-9+/=]+',  # DOCX header en base64
        ],
        'yaml': [
            r'apiVersion:\s*\w+',
            r'kind:\s*\w+',
            r'---\n',
        ],
        'json': [
            r'^\s*[\{\[].*[\}\]]\s*$',
        ],
        'txt': [
            r'.*',  # Fallback para texto plano
        ]
    }
    
    def __init__(self, project_name: str = "default"):
        self.project_name = project_name
        self.processed_files = []
    
    def detect_file_type(self, content: str) -> str:
        """Detecta el tipo de archivo basado en patrones"""
        logger.info(f"🔍 Detectando tipo de archivo para contenido de {len(content)} caracteres")
        
        for file_type, patterns in self.FILE_PATTERNS.items():
            if file_type == 'txt':  # Skip txt as it's fallback
                continue
                
            for pattern in patterns:
                if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                    logger.info(f"✅ Tipo detectado: {file_type}")
                    return file_type
        
        logger.info(f"📄 Tipo por defecto: txt")
        return 'txt'
    
    def extract_file_content(self, content: str, file_type: str) -> bytes:
        """Extrae el contenido del archivo según su tipo"""
        logger.info(f"📤 Extrayendo contenido para tipo: {file_type}")
        
        try:
            if file_type == 'png':
                # Buscar base64 de PNG
                base64_match = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', content)
                if base64_match:
                    return base64.b64decode(base64_match.group(1))
                
                # Buscar PNG header en base64
                png_match = re.search(r'(iVBORw0KGgo[A-Za-z0-9+/=]+)', content)
                if png_match:
                    return base64.b64decode(png_match.group(1))
                
                # Buscar hex
                hex_match = re.search(r'(89504e47[0-9a-fA-F]+)', content)
                if hex_match:
                    return bytes.fromhex(hex_match.group(1))
            
            elif file_type == 'svg':
                svg_match = re.search(r'(<svg[^>]*>.*?</svg>)', content, re.DOTALL)
                if svg_match:
                    return svg_match.group(1).encode('utf-8')
            
            elif file_type in ['xlsx', 'docx']:
                # Buscar base64 de Office documents
                office_match = re.search(r'data:application/[^;]+;base64,([A-Za-z0-9+/=]+)', content)
                if office_match:
                    return base64.b64decode(office_match.group(1))
                
                # Buscar Office header en base64
                office_header = re.search(r'(UEsDBBQA[A-Za-z0-9+/=]+)', content)
                if office_header:
                    return base64.b64decode(office_header.group(1))
            
            # Para otros tipos, intentar como texto
            return content.encode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo contenido: {e}")
            return content.encode('utf-8')
    
    def generate_filename(self, tool_name: str, file_type: str) -> str:
        """Genera un nombre de archivo único"""
        timestamp = uuid.uuid4().hex[:8]
        return f"{tool_name}_{timestamp}.{file_type}"
    
    def process_mcp_response(self, tool_name: str, mcp_result: Dict) -> List[Dict]:
        """Procesa la respuesta del MCP y sube archivos a S3"""
        logger.info(f"🔄 Procesando respuesta MCP para {tool_name}")
        
        files_uploaded = []
        
        # Obtener todo el contenido de texto
        raw_text = mcp_result.get('raw_text', '')
        
        if not raw_text:
            logger.warning(f"⚠️ No hay contenido de texto para procesar")
            return files_uploaded
        
        # Verificar si el contenido es JSON válido y extenso
        try:
            parsed_json = json.loads(raw_text)
            if isinstance(parsed_json, dict) and len(raw_text) > 500:
                # Es un JSON extenso, tratarlo como archivo
                logger.info(f"📄 Detectado JSON extenso ({len(raw_text)} chars), procesando como archivo")
                
                # Generar nombre de archivo basado en el contenido
                if 'title' in parsed_json:
                    filename = f"{tool_name}_{parsed_json['title'][:30].replace(' ', '_')}_{uuid.uuid4().hex[:6]}.json"
                else:
                    filename = self.generate_filename(tool_name, 'json')
                
                file_content = raw_text.encode('utf-8')
                
                try:
                    # Subir a S3
                    s3_key = f"mcp-results/{self.project_name}/{filename}"
                    s3_url = upload_to_s3(file_content, s3_key)
                    
                    # Generar URL presignada si está habilitado
                    if USE_PRESIGNED_URLS:
                        presigned_url = generate_presigned_url(s3_key)
                    else:
                        presigned_url = s3_url
                    
                    file_info = {
                        'filename': filename,
                        'file_type': 'json',
                        's3_key': s3_key,
                        's3_url': s3_url,
                        'presigned_url': presigned_url,
                        'size_bytes': len(file_content),
                        'tool_name': tool_name
                    }
                    
                    files_uploaded.append(file_info)
                    self.processed_files.append(file_info)
                    
                    logger.info(f"✅ Archivo JSON subido: {filename} ({len(file_content)} bytes)")
                    return files_uploaded
                    
                except Exception as e:
                    logger.error(f"❌ Error subiendo archivo JSON: {e}")
                    
        except json.JSONDecodeError:
            # No es JSON, continuar con detección normal
            pass
        
        # Detectar tipo de archivo
        file_type = self.detect_file_type(raw_text)
        
        # Extraer contenido del archivo
        file_content = self.extract_file_content(raw_text, file_type)
        
        if len(file_content) == 0:
            logger.warning(f"⚠️ No se pudo extraer contenido del archivo")
            return files_uploaded
        
        # Generar nombre de archivo
        filename = self.generate_filename(tool_name, file_type)
        
        try:
            # Subir a S3
            s3_key = f"mcp-results/{self.project_name}/{filename}"
            s3_url = upload_to_s3(file_content, s3_key)
            
            # Generar URL presignada si está habilitado
            if USE_PRESIGNED_URLS:
                presigned_url = generate_presigned_url(s3_key)
            else:
                presigned_url = s3_url
            
            file_info = {
                'filename': filename,
                'file_type': file_type,
                's3_key': s3_key,
                's3_url': s3_url,
                'presigned_url': presigned_url,
                'size_bytes': len(file_content),
                'tool_name': tool_name
            }
            
            files_uploaded.append(file_info)
            self.processed_files.append(file_info)
            
            logger.info(f"✅ Archivo subido: {filename} ({len(file_content)} bytes)")
            
        except Exception as e:
            logger.error(f"❌ Error subiendo archivo: {e}")
        
        return files_uploaded
    
    def process_multiple_files(self, content: str, tool_name: str) -> List[Dict]:
        """Procesa múltiples archivos en una respuesta"""
        logger.info(f"🔄 Buscando múltiples archivos en respuesta de {tool_name}")
        
        files_uploaded = []
        
        # Buscar múltiples patrones de archivos
        for file_type, patterns in self.FILE_PATTERNS.items():
            if file_type == 'txt':
                continue
                
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
                for i, match in enumerate(matches):
                    try:
                        file_content = self.extract_file_content(match.group(0), file_type)
                        if len(file_content) > 0:
                            filename = f"{tool_name}_{file_type}_{i+1}_{uuid.uuid4().hex[:6]}.{file_type}"
                            s3_key = f"mcp-results/{self.project_name}/{filename}"
                            s3_url = upload_to_s3(file_content, s3_key)
                            
                            if USE_PRESIGNED_URLS:
                                presigned_url = generate_presigned_url(s3_key)
                            else:
                                presigned_url = s3_url
                            
                            file_info = {
                                'filename': filename,
                                'file_type': file_type,
                                's3_key': s3_key,
                                's3_url': s3_url,
                                'presigned_url': presigned_url,
                                'size_bytes': len(file_content),
                                'tool_name': tool_name
                            }
                            
                            files_uploaded.append(file_info)
                            logger.info(f"✅ Archivo múltiple subido: {filename}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error procesando archivo múltiple: {e}")
        
        return files_uploaded
    
    def get_processed_files(self) -> List[Dict]:
        """Retorna la lista de archivos procesados"""
        return self.processed_files
    
    def clear_processed_files(self):
        """Limpia la lista de archivos procesados"""
        self.processed_files = []
