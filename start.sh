#!/bin/bash

echo "🚀 Iniciando Bedrock Playground"
echo "================================"

# Instalar dependencias
echo "📦 Instalando dependencias..."
cd /home/ec2-user/bedrock-chat-new/backend
pip3 install -r requirements.txt

# Iniciar backend
echo "🔧 Iniciando backend..."
cd /home/ec2-user/bedrock-chat-new/backend
python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!

sleep 3

# Iniciar frontend
echo "🌐 Iniciando frontend..."
cd /home/ec2-user/bedrock-chat-new/frontend
python3 server.py > frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 2

echo "✅ Sistema iniciado:"
echo "   Backend: http://localhost:8001"
echo "   Frontend: http://localhost:3003"
echo "   Docs: http://localhost:8001/docs"
echo ""
echo "PIDs: Backend=$BACKEND_PID, Frontend=$FRONTEND_PID"
echo ""
echo "Para detener:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
