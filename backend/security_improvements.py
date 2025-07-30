# MEJORAS DE SEGURIDAD PARA BEDROCK PLAYGROUND

import hashlib
import hmac
import jwt
import time
from typing import Optional
import re

# 1. AUTENTICACIÓN Y AUTORIZACIÓN
class AuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.token_expiry = 3600  # 1 hora
    
    def generate_token(self, user_id: str, permissions: list) -> str:
        payload = {
            "user_id": user_id,
            "permissions": permissions,
            "exp": time.time() + self.token_expiry,
            "iat": time.time()
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def has_permission(self, token: str, required_permission: str) -> bool:
        payload = self.verify_token(token)
        if not payload:
            return False
        return required_permission in payload.get("permissions", [])

# 2. VALIDACIÓN DE ENTRADA
class InputValidator:
    def __init__(self):
        self.max_message_length = 10000
        self.max_tokens = 4000
        self.allowed_models = [
            "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "amazon.nova-pro-v1:0"
        ]
        
        # Patrones peligrosos
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'__import__',
            r'subprocess',
            r'os\.system'
        ]
    
    def validate_message(self, message: str) -> tuple[bool, str]:
        if not message or not message.strip():
            return False, "Mensaje vacío"
        
        if len(message) > self.max_message_length:
            return False, f"Mensaje demasiado largo (máximo {self.max_message_length} caracteres)"
        
        # Verificar patrones peligrosos
        for pattern in self.dangerous_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return False, "Contenido potencialmente peligroso detectado"
        
        return True, "Válido"
    
    def validate_model(self, model: str) -> bool:
        return model in self.allowed_models
    
    def validate_temperature(self, temperature: float) -> bool:
        return 0.0 <= temperature <= 1.0
    
    def validate_max_tokens(self, max_tokens: int) -> bool:
        return 1 <= max_tokens <= self.max_tokens

# 3. SANITIZACIÓN DE RESPUESTAS
class ResponseSanitizer:
    def __init__(self):
        self.sensitive_patterns = [
            r'aws_access_key_id\s*=\s*[A-Z0-9]{20}',
            r'aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}',
            r'password\s*=\s*[^\s]+',
            r'token\s*=\s*[^\s]+',
            r'api_key\s*=\s*[^\s]+',
        ]
    
    def sanitize_response(self, response: str) -> str:
        sanitized = response
        
        # Remover información sensible
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Escapar HTML para prevenir XSS
        sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
        
        return sanitized

# 4. AUDIT LOGGING
class AuditLogger:
    def __init__(self):
        self.log_file = "/var/log/bedrock-playground/audit.log"
    
    def log_request(self, user_id: str, endpoint: str, params: dict, ip_address: str):
        log_entry = {
            "timestamp": time.time(),
            "user_id": user_id,
            "endpoint": endpoint,
            "ip_address": ip_address,
            "params_hash": hashlib.sha256(str(params).encode()).hexdigest()
        }
        
        # En producción, usar logging estructurado
        print(f"AUDIT: {log_entry}")
    
    def log_response(self, user_id: str, success: bool, response_time: float):
        log_entry = {
            "timestamp": time.time(),
            "user_id": user_id,
            "success": success,
            "response_time": response_time
        }
        
        print(f"AUDIT: {log_entry}")

# 5. ENCRIPTACIÓN DE DATOS SENSIBLES
class DataEncryption:
    def __init__(self, key: bytes):
        self.key = key
    
    def encrypt_system_prompt(self, prompt: str) -> str:
        # En producción usar Fernet o similar
        return prompt  # Placeholder
    
    def decrypt_system_prompt(self, encrypted_prompt: str) -> str:
        # En producción usar Fernet o similar
        return encrypted_prompt  # Placeholder

# 6. CORS SEGURO
class SecureCORS:
    def __init__(self):
        self.allowed_origins = [
            "https://bedrock-playground.danielingram.shop",
            "https://localhost:3005"
        ]
        self.allowed_methods = ["GET", "POST", "OPTIONS"]
        self.allowed_headers = ["Content-Type", "Authorization"]
    
    def is_origin_allowed(self, origin: str) -> bool:
        return origin in self.allowed_origins

# 7. DETECCIÓN DE ANOMALÍAS
class AnomalyDetector:
    def __init__(self):
        self.request_patterns = {}
        self.suspicious_threshold = 10  # requests per minute
    
    def analyze_request_pattern(self, ip_address: str, endpoint: str) -> bool:
        key = f"{ip_address}:{endpoint}"
        now = time.time()
        
        if key not in self.request_patterns:
            self.request_patterns[key] = []
        
        # Limpiar requests antiguos (últimos 60 segundos)
        self.request_patterns[key] = [
            req_time for req_time in self.request_patterns[key]
            if now - req_time < 60
        ]
        
        self.request_patterns[key].append(now)
        
        # Verificar si excede el threshold
        return len(self.request_patterns[key]) > self.suspicious_threshold

# 8. CONFIGURACIÓN DE SEGURIDAD
class SecurityConfig:
    def __init__(self):
        self.settings = {
            "max_request_size": 1024 * 1024,  # 1MB
            "request_timeout": 30,  # 30 segundos
            "max_concurrent_requests": 100,
            "enable_rate_limiting": True,
            "enable_audit_logging": True,
            "enable_input_validation": True,
            "enable_response_sanitization": True,
            "jwt_secret": "your-secret-key-here",  # En producción usar variable de entorno
            "encryption_key": b"your-encryption-key-here"  # En producción usar KMS
        }
    
    def get(self, key: str, default=None):
        return self.settings.get(key, default)

# 9. MIDDLEWARE DE SEGURIDAD
class SecurityMiddleware:
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.auth_manager = AuthManager(config.get("jwt_secret"))
        self.input_validator = InputValidator()
        self.response_sanitizer = ResponseSanitizer()
        self.audit_logger = AuditLogger()
        self.anomaly_detector = AnomalyDetector()
    
    async def process_request(self, request, call_next):
        # 1. Verificar tamaño de request
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.config.get("max_request_size"):
            return {"error": "Request too large", "status_code": 413}
        
        # 2. Detectar anomalías
        client_ip = request.client.host
        if self.anomaly_detector.analyze_request_pattern(client_ip, request.url.path):
            return {"error": "Suspicious activity detected", "status_code": 429}
        
        # 3. Procesar request
        start_time = time.time()
        response = await call_next(request)
        response_time = time.time() - start_time
        
        # 4. Audit logging
        self.audit_logger.log_response("anonymous", True, response_time)
        
        return response
