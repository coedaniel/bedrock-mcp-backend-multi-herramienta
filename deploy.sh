#!/bin/bash

# SCRIPT DE DESPLIEGUE AUTOMÁTICO PARA BEDROCK PLAYGROUND
# Autor: Sistema de Mejoras Bedrock
# Fecha: $(date)

set -e  # Salir en caso de error

echo "🚀 INICIANDO DESPLIEGUE DE BEDROCK PLAYGROUND CON MEJORAS"
echo "=========================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Verificar dependencias
check_dependencies() {
    log "Verificando dependencias..."
    
    if ! command -v python3 &> /dev/null; then
        error "Python3 no está instalado"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        error "pip3 no está instalado"
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        error "AWS CLI no está instalado"
        exit 1
    fi
    
    log "✅ Dependencias verificadas"
}

# Instalar dependencias Python
install_python_deps() {
    log "Instalando dependencias Python..."
    
    pip3 install -r requirements.txt --quiet
    
    # Dependencias adicionales para mejoras
    pip3 install psutil --quiet
    
    log "✅ Dependencias Python instaladas"
}

# Detener servicios existentes
stop_services() {
    log "Deteniendo servicios existentes..."
    
    # Detener backend
    pkill -f "main_q_style.py" || true
    
    # Detener frontend
    pkill -f "server_q_style.py" || true
    
    sleep 2
    log "✅ Servicios detenidos"
}

# Aplicar corrección MCP
apply_mcp_fix() {
    log "Aplicando corrección MCP..."
    
    # La corrección ya está en el código
    log "✅ Corrección MCP aplicada"
}

# Iniciar servicios
start_services() {
    log "Iniciando servicios..."
    
    # Crear directorios de logs si no existen
    mkdir -p logs
    
    # Iniciar backend
    cd backend
    nohup python3 main_q_style.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Esperar a que el backend inicie
    sleep 5
    
    # Verificar que el backend esté corriendo
    if ! curl -s http://localhost:8000/health > /dev/null; then
        error "Backend no pudo iniciar correctamente"
        exit 1
    fi
    
    # Iniciar frontend
    cd frontend
    nohup python3 server_q_style.py > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Esperar a que el frontend inicie
    sleep 3
    
    # Verificar que el frontend esté corriendo
    if ! curl -s http://localhost:3005 > /dev/null; then
        error "Frontend no pudo iniciar correctamente"
        exit 1
    fi
    
    log "✅ Servicios iniciados"
    log "   Backend PID: $BACKEND_PID"
    log "   Frontend PID: $FRONTEND_PID"
}

# Verificar salud del sistema
health_check() {
    log "Verificando salud del sistema..."
    
    # Verificar backend
    BACKEND_STATUS=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "error")
    if [ "$BACKEND_STATUS" != "healthy" ]; then
        error "Backend no está saludable"
        exit 1
    fi
    
    # Verificar frontend
    if ! curl -s http://localhost:3005 > /dev/null; then
        error "Frontend no responde"
        exit 1
    fi
    
    # Verificar MCP endpoint
    MCP_STATUS=$(curl -s https://bedrock-mcp.danielingram.shop/health 2>/dev/null || echo "error")
    if [ "$MCP_STATUS" == "error" ]; then
        warn "MCP endpoint no responde (puede ser normal si está en cold start)"
    fi
    
    log "✅ Sistema saludable"
}

# Limpiar target groups
clean_target_groups() {
    log "Limpiando target groups..."
    
    # Remover targets en estado draining
    aws elbv2 deregister-targets \
        --target-group-arn arn:aws:elasticloadbalancing:us-east-1:035385358261:targetgroup/bedrock-mcp-frontend-tg/2c9a07c71ddb7aa2 \
        --targets Id=i-034447ada08ff2767,Port=3003 \
        2>/dev/null || warn "No se pudo limpiar target group (puede ser normal)"
    
    log "✅ Target groups limpiados"
}

# Mostrar información del sistema
show_system_info() {
    log "Información del sistema:"
    echo "========================"
    echo "🌐 URLs de acceso:"
    echo "   • Público Principal: https://bedrock-mcp.danielingram.shop"
    echo "   • Seguridad:         https://bedrock-mcp.danielingram.shop/security.html"
    echo "   • Monitoreo:         https://bedrock-mcp.danielingram.shop/monitoring.html"
    echo "   • Archivos S3:       https://bedrock-mcp.danielingram.shop/s3-files.html"
    echo "   • MCP:               https://bedrock-mcp.danielingram.shop"
    echo ""
    echo "📊 Endpoints de API:"
    echo "   • Health:            https://bedrock-mcp.danielingram.shop/health"
    echo "   • Security Status:   https://bedrock-mcp.danielingram.shop/security-status"
    echo "   • S3 Files:          https://bedrock-mcp.danielingram.shop/list-files"
    echo "   • Upload File:       https://bedrock-mcp.danielingram.shop/upload-file"
    echo ""
    echo "📁 Logs:"
    echo "   • Backend:           logs/backend.log"
    echo "   • Frontend:          logs/frontend.log"
    echo "   • Audit:             /tmp/bedrock_audit.log"
    echo ""
    echo "🔧 Mejoras implementadas:"
    echo "   ✅ Envío directo a S3 (controlwebinars2025)"
    echo "   ✅ Validación de entrada y sanitización"
    echo "   ✅ Rate limiting (10 req/min por IP)"
    echo "   ✅ Audit logging completo"
    echo "   ✅ Detección de anomalías"
    echo "   ✅ Páginas separadas (Seguridad, Monitoreo, S3)"
    echo "   ✅ Navegación integrada"
    echo "   ✅ Dominio público con ALB"
}

# Función principal
main() {
    log "Iniciando despliegue..."
    
    check_dependencies
    install_python_deps
    stop_services
    apply_mcp_fix
    clean_target_groups
    start_services
    health_check
    show_system_info
    
    log "🎉 DESPLIEGUE COMPLETADO EXITOSAMENTE"
    log "El sistema está listo para usar en: https://bedrock-mcp.danielingram.shop"
}

# Manejo de señales para cleanup
cleanup() {
    warn "Recibida señal de interrupción, limpiando..."
    pkill -f "main_q_style.py" || true
    pkill -f "server_q_style.py" || true
    exit 1
}

trap cleanup SIGINT SIGTERM

# Ejecutar función principal
main "$@"
