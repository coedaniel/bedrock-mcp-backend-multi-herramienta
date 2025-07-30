import time
import hashlib
import json
import logging
from typing import Dict, List, Optional
from collections import defaultdict, deque
import re

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.input_validator = InputValidator()
        self.audit_logger = AuditLogger()
        self.anomaly_detector = AnomalyDetector()

    def validate_request(self, request_data: dict, client_ip: str) -> dict:
        """Validar request completo"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # 1. Rate limiting
        if not self.rate_limiter.allow_request(client_ip):
            result["valid"] = False
            result["errors"].append("Rate limit exceeded")

        # 2. Validar entrada
        validation_result = self.input_validator.validate_input(request_data)
        if not validation_result["valid"]:
            result["valid"] = False
            result["errors"].extend(validation_result["errors"])

        # 3. Detectar anomalías
        anomaly_result = self.anomaly_detector.check_request(request_data, client_ip)
        if anomaly_result["suspicious"]:
            result["warnings"].extend(anomaly_result["warnings"])

        # 4. Log de auditoría
        self.audit_logger.log_request(request_data, client_ip, result)

        return result

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests = defaultdict(deque)

    def allow_request(self, client_ip: str) -> bool:
        """Verificar si se permite el request"""
        now = time.time()
        client_requests = self.requests[client_ip]

        # Limpiar requests antiguos
        while client_requests and client_requests[0] < now - self.window_seconds:
            client_requests.popleft()

        # Verificar límite
        if len(client_requests) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False

        # Agregar request actual
        client_requests.append(now)
        return True

    def get_remaining_requests(self, client_ip: str) -> int:
        """Obtener requests restantes"""
        now = time.time()
        client_requests = self.requests[client_ip]

        # Limpiar requests antiguos
        while client_requests and client_requests[0] < now - self.window_seconds:
            client_requests.popleft()

        return max(0, self.max_requests - len(client_requests))

class InputValidator:
    def __init__(self):
        self.max_message_length = 10000
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS básico
            r'javascript:',               # JavaScript URLs
            r'on\w+\s*=',                # Event handlers
            r'eval\s*\(',                # eval() calls
            r'exec\s*\(',                # exec() calls
            r'import\s+os',              # OS imports
            r'__import__',               # Dynamic imports
        ]

    def validate_input(self, request_data: dict) -> dict:
        """Validar datos de entrada"""
        result = {
            "valid": True,
            "errors": [],
            "sanitized_data": {}
        }

        try:
            # Validar mensaje
            message = request_data.get('message', '')
            if not message or not isinstance(message, str):
                result["valid"] = False
                result["errors"].append("Message is required and must be string")
                return result

            # Verificar longitud
            if len(message) > self.max_message_length:
                result["valid"] = False
                result["errors"].append(f"Message too long (max {self.max_message_length} chars)")
                return result

            # Verificar patrones peligrosos
            for pattern in self.dangerous_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    result["valid"] = False
                    result["errors"].append("Potentially dangerous content detected")
                    logger.warning(f"Dangerous pattern detected: {pattern}")
                    return result

            # Sanitizar datos
            result["sanitized_data"] = {
                "message": self.sanitize_string(message),
                "model": request_data.get('model', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                "temperature": max(0.0, min(1.0, float(request_data.get('temperature', 0.7)))),
                "max_tokens": max(1, min(4000, int(request_data.get('max_tokens', 2000))))
            }

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Validation error: {str(e)}")

        return result

    def sanitize_string(self, text: str) -> str:
        """Sanitizar string básico"""
        # Remover caracteres de control
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Escapar HTML básico
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        return text.strip()

class AuditLogger:
    def __init__(self):
        self.log_file = "/tmp/bedrock_audit.log"

    def log_request(self, request_data: dict, client_ip: str, validation_result: dict):
        """Log de auditoría"""
        try:
            log_entry = {
                "timestamp": time.time(),
                "client_ip": client_ip,
                "message_hash": hashlib.sha256(
                    request_data.get('message', '').encode()
                ).hexdigest()[:16],
                "model": request_data.get('model'),
                "validation_passed": validation_result["valid"],
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", [])
            }

            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            logger.error(f"Error writing audit log: {str(e)}")

    def get_recent_logs(self, hours: int = 24) -> List[dict]:
        """Obtener logs recientes"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            logs = []

            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get('timestamp', 0) > cutoff_time:
                            logs.append(log_entry)
                    except:
                        continue

            return sorted(logs, key=lambda x: x.get('timestamp', 0), reverse=True)

        except Exception as e:
            logger.error(f"Error reading audit logs: {str(e)}")
            return []

class AnomalyDetector:
    def __init__(self):
        self.request_patterns = defaultdict(list)
        self.suspicious_keywords = [
            'hack', 'exploit', 'vulnerability', 'injection', 'bypass',
            'admin', 'root', 'password', 'token', 'secret'
        ]

    def check_request(self, request_data: dict, client_ip: str) -> dict:
        """Detectar patrones anómalos"""
        result = {
            "suspicious": False,
            "warnings": [],
            "score": 0
        }

        message = request_data.get('message', '').lower()

        # 1. Verificar palabras sospechosas
        suspicious_count = sum(1 for keyword in self.suspicious_keywords if keyword in message)
        if suspicious_count > 2:
            result["suspicious"] = True
            result["warnings"].append(f"Multiple suspicious keywords detected ({suspicious_count})")
            result["score"] += suspicious_count * 10

        # 2. Verificar longitud anómala
        if len(message) > 5000:
            result["warnings"].append("Unusually long message")
            result["score"] += 5

        # 3. Verificar repetición de patrones
        self.request_patterns[client_ip].append({
            "timestamp": time.time(),
            "message_hash": hashlib.sha256(message.encode()).hexdigest()[:16]
        })

        # Limpiar patrones antiguos (últimas 24 horas)
        cutoff = time.time() - 86400
        self.request_patterns[client_ip] = [
            p for p in self.request_patterns[client_ip] 
            if p["timestamp"] > cutoff
        ]

        # Verificar duplicados
        recent_hashes = [p["message_hash"] for p in self.request_patterns[client_ip][-10:]]
        if len(set(recent_hashes)) < len(recent_hashes) * 0.7:  # 70% únicos
            result["warnings"].append("Repetitive request patterns detected")
            result["score"] += 15

        if result["score"] > 20:
            result["suspicious"] = True

        return result

# Instancia global
security_manager = SecurityManager()
