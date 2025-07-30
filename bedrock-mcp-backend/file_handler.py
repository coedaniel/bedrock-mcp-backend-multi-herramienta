"""
🗂️ File Handler - Interceptor y procesador de archivos generados por MCP
Maneja la detección, descarga y subida a S3 de archivos generados
"""

import os
import re
import uuid
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin
import mimetypes
import logging

from s3_utils import upload_to_s3, generate_presigned_url
from config import Config

logger = logging.getLogger(__name__)

class FileHandler:
    """
    🔧 Maneja la interceptación y procesamiento de archivos generados por MCP
    """
    
    def __init__(self):
        self.config = Config()
        self.supported_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.svg',  # Imágenes
            '.pdf', '.docx', '.doc',                   # Documentos
            '.xlsx', '.xls', '.csv',                   # Hojas de cálculo
            '.txt', '.md', '.json', '.xml'             # Texto/Data
        }
        
    async def process_mcp_response(self, response: Dict, project_name: str = "default") -> Dict:
        """
        🔍 Procesa respuesta MCP buscando archivos generados
        """
        try:
            # Buscar archivos en el contenido de la respuesta
            files_found = await self._extract_file_references(response)
            
            if not files_found:
                logger.info("📄 No se encontraron archivos en la respuesta MCP")
                return response
                
            logger.info(f"📁 Encontrados {len(files_found)} archivos para procesar")
            
            # Procesar cada archivo encontrado
            processed_files = []
            for file_info in files_found:
                try:
                    processed_file = await self._process_single_file(file_info, project_name)
                    if processed_file:
                        processed_files.append(processed_file)
                except Exception as e:
                    logger.error(f"❌ Error procesando archivo {file_info.get('path', 'unknown')}: {str(e)}")
            
            # Actualizar respuesta con información de archivos procesados
            if processed_files:
                response = await self._update_response_with_files(response, processed_files)
                
            return response
            
        except Exception as e:
            logger.error(f"💥 Error procesando respuesta MCP: {str(e)}")
            return response
    
    async def _extract_file_references(self, response: Dict) -> List[Dict]:
        """
        🔍 Extrae referencias a archivos de la respuesta MCP
        """
        files_found = []
        
        # Buscar en contenido de texto
        content_items = response.get('content', [])
        for item in content_items:
            if item.get('type') == 'text':
                text_content = item.get('text', '')
                file_refs = await self._find_file_paths_in_text(text_content)
                files_found.extend(file_refs)
        
        # Buscar en toolResult si existe
        tool_result = response.get('toolResult', {})
        if tool_result:
            tool_content = tool_result.get('content', [])
            for item in tool_content:
                if item.get('type') == 'text':
                    text_content = item.get('text', '')
                    file_refs = await self._find_file_paths_in_text(text_content)
                    files_found.extend(file_refs)
        
        return files_found
    
    async def _find_file_paths_in_text(self, text: str) -> List[Dict]:
        """
        🔍 Busca rutas de archivos en texto usando patrones
        """
        files_found = []
        
        # Patrones para detectar archivos
        patterns = [
            r'(?:saved to|generated at|created at|output file|file path):\s*([^\s\n]+)',
            r'(?:file|diagram|image|document):\s*([^\s\n]+\.\w+)',
            r'(?:\/[^\s\n]*\/[^\s\n]*\.\w+)',  # Rutas absolutas
            r'(?:\.[\/\\][^\s\n]*\.\w+)',      # Rutas relativas
            r'(?:generated-diagrams\/[^\s\n]+)',  # Directorio específico
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                file_path = match.group(1) if match.groups() else match.group(0)
                file_path = file_path.strip('"\'')
                
                # Verificar extensión soportada
                _, ext = os.path.splitext(file_path.lower())
                if ext in self.supported_extensions:
                    files_found.append({
                        'path': file_path,
                        'extension': ext,
                        'detected_pattern': pattern
                    })
        
        return files_found
    
    async def _process_single_file(self, file_info: Dict, project_name: str) -> Optional[Dict]:
        """
        📁 Procesa un archivo individual
        """
        file_path = file_info['path']
        extension = file_info['extension']
        
        logger.info(f"🔄 Procesando archivo: {file_path}")
        
        try:
            # Intentar diferentes métodos de acceso al archivo
            file_content = await self._get_file_content(file_path)
            
            if not file_content:
                logger.warning(f"⚠️ No se pudo obtener contenido del archivo: {file_path}")
                return None
            
            # Generar nombre único para S3
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            original_name = os.path.basename(file_path)
            s3_key = f"archivos/{project_name}/{timestamp}_{unique_id}_{original_name}"
            
            # Determinar content type
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # Subir a S3
            s3_url = await upload_to_s3(
                content=file_content,
                key=s3_key,
                content_type=content_type
            )
            
            if not s3_url:
                logger.error(f"❌ Error subiendo archivo a S3: {file_path}")
                return None
            
            # Generar URL presignada si está habilitado
            presigned_url = None
            if self.config.USE_PRESIGNED_URLS:
                presigned_url = generate_presigned_url(s3_key)
            
            processed_file = {
                'original_path': file_path,
                'filename': original_name,
                'extension': extension,
                'content_type': content_type,
                's3_key': s3_key,
                's3_url': s3_url,
                'presigned_url': presigned_url,
                'size_bytes': len(file_content),
                'processed_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Archivo procesado exitosamente: {original_name} → {s3_key}")
            return processed_file
            
        except Exception as e:
            logger.error(f"💥 Error procesando archivo {file_path}: {str(e)}")
            return None
    
    async def _get_file_content(self, file_path: str) -> Optional[bytes]:
        """
        📥 Obtiene contenido del archivo usando diferentes métodos
        """
        methods = [
            self._read_local_file,
            self._download_from_url,
            self._read_from_mcp_server
        ]
        
        for method in methods:
            try:
                content = await method(file_path)
                if content:
                    return content
            except Exception as e:
                logger.debug(f"🔄 Método {method.__name__} falló para {file_path}: {str(e)}")
                continue
        
        return None
    
    async def _read_local_file(self, file_path: str) -> Optional[bytes]:
        """
        📂 Lee archivo del sistema de archivos local
        """
        if not os.path.isfile(file_path):
            # Intentar rutas relativas comunes
            possible_paths = [
                file_path,
                os.path.join('/tmp', os.path.basename(file_path)),
                os.path.join('/app', file_path.lstrip('/')),
                os.path.join(os.getcwd(), file_path.lstrip('./'))
            ]
            
            for path in possible_paths:
                if os.path.isfile(path):
                    file_path = path
                    break
            else:
                return None
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    async def _download_from_url(self, file_path: str) -> Optional[bytes]:
        """
        🌐 Descarga archivo desde URL
        """
        if not (file_path.startswith('http://') or file_path.startswith('https://')):
            return None
        
        async with aiohttp.ClientSession() as session:
            async with session.get(file_path) as response:
                if response.status == 200:
                    return await response.read()
        
        return None
    
    async def _read_from_mcp_server(self, file_path: str) -> Optional[bytes]:
        """
        🔗 Intenta leer archivo desde MCP server
        """
        # Construir URL del MCP server
        base_url = self.config.MCP_BASE_URL.replace('/bedrock/tool-use', '')
        file_url = urljoin(base_url, file_path.lstrip('/'))
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception:
            pass
        
        return None
    
    async def _update_response_with_files(self, response: Dict, processed_files: List[Dict]) -> Dict:
        """
        📝 Actualiza la respuesta con información de archivos procesados
        """
        # Crear resumen de archivos
        files_summary = []
        for file_info in processed_files:
            summary = f"📁 **{file_info['filename']}**\n"
            summary += f"   • Tamaño: {file_info['size_bytes']:,} bytes\n"
            summary += f"   • Tipo: {file_info['content_type']}\n"
            
            if file_info['presigned_url']:
                summary += f"   • 🔗 [Descargar]({file_info['presigned_url']})\n"
            else:
                summary += f"   • 📍 S3: {file_info['s3_key']}\n"
            
            files_summary.append(summary)
        
        # Agregar información de archivos a la respuesta
        files_text = "\n\n🗂️ **Archivos Generados:**\n\n" + "\n".join(files_summary)
        
        # Actualizar contenido existente
        if 'toolResult' in response:
            content = response['toolResult'].get('content', [])
            if content and content[-1].get('type') == 'text':
                content[-1]['text'] += files_text
            else:
                content.append({'type': 'text', 'text': files_text})
        else:
            content = response.get('content', [])
            if content and content[-1].get('type') == 'text':
                content[-1]['text'] += files_text
            else:
                content.append({'type': 'text', 'text': files_text})
        
        # Agregar metadatos de archivos
        response['_files_processed'] = processed_files
        
        return response

# Instancia global del file handler
file_handler = FileHandler()
