# MEJORAS DE RENDIMIENTO PARA BEDROCK PLAYGROUND

import asyncio
import time
from functools import lru_cache
import redis
import json

# 1. CACHE DE RESPUESTAS FRECUENTES
class ResponseCache:
    def __init__(self):
        # En producción usar Redis
        self.cache = {}
        self.ttl = 3600  # 1 hora
    
    def get_cache_key(self, message: str, model: str, temperature: float) -> str:
        return f"{hash(message)}_{model}_{temperature}"
    
    def get(self, key: str):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: dict):
        self.cache[key] = (value, time.time())

# 2. RATE LIMITING
class RateLimiter:
    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Limpiar requests antiguos
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window
        ]
        
        if len(self.requests[client_ip]) < self.max_requests:
            self.requests[client_ip].append(now)
            return True
        return False

# 3. CONNECTION POOLING
class ConnectionManager:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

# 4. ASYNC PROCESSING
class AsyncProcessor:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
    
    async def process_with_limit(self, coro):
        async with self.semaphore:
            return await coro

# 5. HEALTH CHECK MEJORADO
class HealthChecker:
    def __init__(self):
        self.last_check = {}
        self.check_interval = 30  # 30 segundos
    
    async def check_dependencies(self):
        checks = {
            "bedrock": self.check_bedrock(),
            "mcp": self.check_mcp(),
            "database": self.check_database()
        }
        
        results = {}
        for name, check in checks.items():
            try:
                results[name] = await asyncio.wait_for(check, timeout=5)
            except asyncio.TimeoutError:
                results[name] = {"status": "timeout", "healthy": False}
            except Exception as e:
                results[name] = {"status": "error", "healthy": False, "error": str(e)}
        
        return results
    
    async def check_bedrock(self):
        # Implementar check de Bedrock
        return {"status": "healthy", "healthy": True}
    
    async def check_mcp(self):
        # Implementar check de MCP
        return {"status": "healthy", "healthy": True}
    
    async def check_database(self):
        # Implementar check de base de datos si aplica
        return {"status": "healthy", "healthy": True}

# 6. LOGGING ESTRUCTURADO
import logging
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

# 7. MÉTRICAS Y MONITOREO
class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_error": 0,
            "response_times": [],
            "active_connections": 0
        }
    
    def record_request(self, success: bool, response_time: float):
        self.metrics["requests_total"] += 1
        if success:
            self.metrics["requests_success"] += 1
        else:
            self.metrics["requests_error"] += 1
        
        self.metrics["response_times"].append(response_time)
        # Mantener solo los últimos 1000 tiempos
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
    
    def get_stats(self):
        response_times = self.metrics["response_times"]
        return {
            **self.metrics,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "success_rate": self.metrics["requests_success"] / max(self.metrics["requests_total"], 1) * 100
        }

# 8. CIRCUIT BREAKER PATTERN
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e
