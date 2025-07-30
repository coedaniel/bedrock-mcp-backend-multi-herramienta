import boto3
import json
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class S3FileUploader:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = 'controlwebinars2025'  # Tu bucket existente
        self.base_path = 'proyectos/bedrock-playground/generated-files'
        
    def upload_file_content(self, content: str, file_type: str, filename: str = None) -> str:
        """
        Sube contenido directamente a S3
        
        Args:
            content: Contenido del archivo
            file_type: Tipo de archivo (diagram, document, etc.)
            filename: Nombre del archivo (opcional)
            
        Returns:
            URL del archivo en S3
        """
        try:
            # Generar nombre único si no se proporciona
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_id = str(uuid.uuid4())[:8]
                filename = f"{file_type}_{timestamp}_{unique_id}"
            
            # Determinar extensión basada en tipo
            extensions = {
                'diagram': '.png',
                'document': '.md',
                'json': '.json',
                'text': '.txt',
                'html': '.html'
            }
            
            if not filename.endswith(tuple(extensions.values())):
                filename += extensions.get(file_type, '.txt')
            
            # Construir key de S3
            s3_key = f"{self.base_path}/{file_type}/{filename}"
            
            # Determinar content type
            content_types = {
                '.png': 'image/png',
                '.md': 'text/markdown',
                '.json': 'application/json',
                '.txt': 'text/plain',
                '.html': 'text/html'
            }
            
            file_ext = '.' + filename.split('.')[-1]
            content_type = content_types.get(file_ext, 'text/plain')
            
            # Subir a S3
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = content
                
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content_bytes,
                ContentType=content_type,
                ServerSideEncryption='AES256',
                Metadata={
                    'uploaded_by': 'bedrock-playground',
                    'upload_time': datetime.now().isoformat(),
                    'file_type': file_type
                }
            )
            
            # Construir URL pública
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            logger.info(f"File uploaded successfully to S3: {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    def upload_json_data(self, data: dict, filename: str = None) -> str:
        """Sube datos JSON a S3"""
        json_content = json.dumps(data, indent=2, ensure_ascii=False)
        return self.upload_file_content(json_content, 'json', filename)
    
    def upload_markdown(self, markdown_content: str, filename: str = None) -> str:
        """Sube contenido Markdown a S3"""
        return self.upload_file_content(markdown_content, 'document', filename)
    
    def upload_diagram(self, image_data: bytes, filename: str = None) -> str:
        """Sube imagen de diagrama a S3"""
        return self.upload_file_content(image_data, 'diagram', filename)
    
    def list_uploaded_files(self, file_type: str = None, limit: int = 50) -> list:
        """Lista archivos subidos"""
        try:
            prefix = f"{self.base_path}/"
            if file_type:
                prefix += f"{file_type}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'url': f"https://{self.bucket_name}.s3.amazonaws.com/{obj['Key']}",
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'filename': obj['Key'].split('/')[-1]
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing S3 files: {str(e)}")
            return []
    
    def delete_file(self, s3_url: str) -> bool:
        """Elimina archivo de S3"""
        try:
            # Extraer key de la URL
            s3_key = s3_url.replace(f"https://{self.bucket_name}.s3.amazonaws.com/", "")
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"File deleted from S3: {s3_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
