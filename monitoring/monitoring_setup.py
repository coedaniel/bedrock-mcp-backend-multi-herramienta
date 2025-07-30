# SISTEMA DE MONITOREO COMPLETO PARA BEDROCK PLAYGROUND

import asyncio
import time
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any
import psutil
import requests

# 1. MÉTRICAS PERSONALIZADAS CLOUDWATCH
class CloudWatchMetrics:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
        self.namespace = 'BedrockPlayground'
    
    def put_metric(self, metric_name: str, value: float, unit: str = 'Count', dimensions: Dict = None):
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': [
                            {'Name': k, 'Value': v} for k, v in (dimensions or {}).items()
                        ]
                    }
                ]
            )
        except Exception as e:
            print(f"Error sending metric {metric_name}: {e}")
    
    def put_custom_metrics(self, metrics: Dict[str, float]):
        """Enviar múltiples métricas de una vez"""
        metric_data = []
        for name, value in metrics.items():
            metric_data.append({
                'MetricName': name,
                'Value': value,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            })
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
        except Exception as e:
            print(f"Error sending custom metrics: {e}")

# 2. HEALTH CHECKS AVANZADOS
class HealthChecker:
    def __init__(self):
        self.endpoints = {
            'backend': 'http://localhost:8001/health',
            'frontend': 'http://localhost:3005',
            'mcp': 'https://bedrock-mcp.danielingram.shop/health',
            'public': 'https://bedrock-playground.danielingram.shop'
        }
        self.timeout = 10
    
    async def check_endpoint(self, name: str, url: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            response = requests.get(url, timeout=self.timeout)
            response_time = time.time() - start_time
            
            return {
                'name': name,
                'url': url,
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code,
                'response_time': response_time,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'name': name,
                'url': url,
                'status': 'unhealthy',
                'error': str(e),
                'response_time': time.time() - start_time,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def check_all_endpoints(self) -> List[Dict[str, Any]]:
        tasks = [
            self.check_endpoint(name, url) 
            for name, url in self.endpoints.items()
        ]
        return await asyncio.gather(*tasks)
    
    def check_system_resources(self) -> Dict[str, float]:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        }

# 3. ALERTAS INTELIGENTES
class AlertManager:
    def __init__(self):
        self.sns = boto3.client('sns', region_name='us-east-1')
        self.topic_arn = 'arn:aws:sns:us-east-1:035385358261:bedrock-playground-alerts'
        self.alert_thresholds = {
            'response_time': 10.0,  # segundos
            'error_rate': 5.0,      # porcentaje
            'cpu_usage': 80.0,      # porcentaje
            'memory_usage': 85.0,   # porcentaje
            'disk_usage': 90.0      # porcentaje
        }
        self.alert_cooldown = {}
        self.cooldown_period = 300  # 5 minutos
    
    def should_send_alert(self, alert_type: str) -> bool:
        now = time.time()
        last_alert = self.alert_cooldown.get(alert_type, 0)
        return now - last_alert > self.cooldown_period
    
    def send_alert(self, alert_type: str, message: str, severity: str = 'WARNING'):
        if not self.should_send_alert(alert_type):
            return
        
        try:
            subject = f"[{severity}] Bedrock Playground Alert: {alert_type}"
            
            self.sns.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=message
            )
            
            self.alert_cooldown[alert_type] = time.time()
            print(f"Alert sent: {subject}")
            
        except Exception as e:
            print(f"Error sending alert: {e}")
    
    def check_thresholds(self, metrics: Dict[str, float]):
        for metric, value in metrics.items():
            threshold = self.alert_thresholds.get(metric)
            if threshold and value > threshold:
                message = f"{metric} is {value:.2f}, exceeding threshold of {threshold}"
                severity = 'CRITICAL' if value > threshold * 1.2 else 'WARNING'
                self.send_alert(metric, message, severity)

# 4. DASHBOARD DE MÉTRICAS
class MetricsDashboard:
    def __init__(self):
        self.metrics_history = []
        self.max_history = 1000
    
    def add_metrics(self, metrics: Dict[str, Any]):
        metrics['timestamp'] = datetime.utcnow().isoformat()
        self.metrics_history.append(metrics)
        
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if datetime.fromisoformat(m['timestamp']) > cutoff
        ]
        
        if not recent_metrics:
            return {}
        
        # Calcular estadísticas
        response_times = [m.get('avg_response_time', 0) for m in recent_metrics]
        error_rates = [m.get('error_rate', 0) for m in recent_metrics]
        
        return {
            'total_requests': sum(m.get('total_requests', 0) for m in recent_metrics),
            'avg_response_time': sum(response_times) / len(response_times),
            'max_response_time': max(response_times),
            'avg_error_rate': sum(error_rates) / len(error_rates),
            'uptime_percentage': len([m for m in recent_metrics if m.get('status') == 'healthy']) / len(recent_metrics) * 100,
            'period_hours': hours,
            'data_points': len(recent_metrics)
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        if format == 'json':
            return json.dumps(self.metrics_history, indent=2)
        elif format == 'csv':
            # Implementar exportación CSV
            pass
        return ""

# 5. MONITOREO CONTINUO
class ContinuousMonitor:
    def __init__(self):
        self.cloudwatch = CloudWatchMetrics()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        self.dashboard = MetricsDashboard()
        self.running = False
        self.check_interval = 60  # 1 minuto
    
    async def monitoring_loop(self):
        while self.running:
            try:
                # 1. Health checks
                health_results = await self.health_checker.check_all_endpoints()
                
                # 2. System resources
                system_metrics = self.health_checker.check_system_resources()
                
                # 3. Compilar métricas
                metrics = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'health_checks': health_results,
                    'system_metrics': system_metrics,
                    'healthy_endpoints': len([h for h in health_results if h['status'] == 'healthy']),
                    'total_endpoints': len(health_results),
                    'avg_response_time': sum(h.get('response_time', 0) for h in health_results) / len(health_results)
                }
                
                # 4. Enviar a CloudWatch
                self.cloudwatch.put_custom_metrics({
                    'HealthyEndpoints': metrics['healthy_endpoints'],
                    'TotalEndpoints': metrics['total_endpoints'],
                    'AvgResponseTime': metrics['avg_response_time'],
                    'CPUUsage': system_metrics['cpu_percent'],
                    'MemoryUsage': system_metrics['memory_percent'],
                    'DiskUsage': system_metrics['disk_percent']
                })
                
                # 5. Verificar alertas
                alert_metrics = {
                    'response_time': metrics['avg_response_time'],
                    'cpu_usage': system_metrics['cpu_percent'],
                    'memory_usage': system_metrics['memory_percent'],
                    'disk_usage': system_metrics['disk_percent']
                }
                self.alert_manager.check_thresholds(alert_metrics)
                
                # 6. Actualizar dashboard
                self.dashboard.add_metrics(metrics)
                
                print(f"Monitoring check completed at {metrics['timestamp']}")
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def start(self):
        self.running = True
        asyncio.create_task(self.monitoring_loop())
        print("Continuous monitoring started")
    
    def stop(self):
        self.running = False
        print("Continuous monitoring stopped")
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'metrics_count': len(self.dashboard.metrics_history),
            'last_check': self.dashboard.metrics_history[-1]['timestamp'] if self.dashboard.metrics_history else None
        }

# 6. CONFIGURACIÓN DE CLOUDWATCH ALARMS
def setup_cloudwatch_alarms():
    cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
    
    alarms = [
        {
            'AlarmName': 'BedrockPlayground-HighResponseTime',
            'ComparisonOperator': 'GreaterThanThreshold',
            'EvaluationPeriods': 2,
            'MetricName': 'AvgResponseTime',
            'Namespace': 'BedrockPlayground',
            'Period': 300,
            'Statistic': 'Average',
            'Threshold': 10.0,
            'ActionsEnabled': True,
            'AlarmActions': ['arn:aws:sns:us-east-1:035385358261:bedrock-playground-alerts'],
            'AlarmDescription': 'Alert when average response time exceeds 10 seconds',
            'Unit': 'Seconds'
        },
        {
            'AlarmName': 'BedrockPlayground-UnhealthyEndpoints',
            'ComparisonOperator': 'LessThanThreshold',
            'EvaluationPeriods': 1,
            'MetricName': 'HealthyEndpoints',
            'Namespace': 'BedrockPlayground',
            'Period': 300,
            'Statistic': 'Average',
            'Threshold': 3.0,
            'ActionsEnabled': True,
            'AlarmActions': ['arn:aws:sns:us-east-1:035385358261:bedrock-playground-alerts'],
            'AlarmDescription': 'Alert when less than 3 endpoints are healthy'
        }
    ]
    
    for alarm in alarms:
        try:
            cloudwatch.put_metric_alarm(**alarm)
            print(f"Created alarm: {alarm['AlarmName']}")
        except Exception as e:
            print(f"Error creating alarm {alarm['AlarmName']}: {e}")

# 7. SCRIPT DE INICIALIZACIÓN
if __name__ == "__main__":
    # Configurar monitoreo
    monitor = ContinuousMonitor()
    
    # Configurar alarms de CloudWatch
    setup_cloudwatch_alarms()
    
    # Iniciar monitoreo
    monitor.start()
    
    try:
        # Mantener el script corriendo
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        monitor.stop()
        print("Monitoring stopped by user")
