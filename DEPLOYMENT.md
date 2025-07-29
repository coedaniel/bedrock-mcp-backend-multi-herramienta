# 🚀 Guía de Despliegue

## 📋 Prerrequisitos

- **Python 3.9+**
- **AWS CLI** configurado
- **Permisos IAM** para S3
- **MCP Server** funcionando

## 🔧 Instalación Local

### 1️⃣ Clonar y Configurar

```bash
# Clonar repositorio
git clone <repo-url>
cd bedrock-mcp-backend-complete

# Backend principal
cd bedrock-mcp-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Variables de Entorno

```bash
# Configurar variables
export AWS_REGION="us-east-1"
export S3_BUCKET="tu-bucket"
export MCP_BASE_URL="https://mcp.danielingram.shop/bedrock/tool-use"
export USE_PRESIGNED_URLS="true"
export LOG_LEVEL="INFO"
```

### 3️⃣ Iniciar Servicios

```bash
# Backend principal (puerto 8000)
./start.sh

# Verificar
curl http://localhost:8000/health
```

## 🐳 Despliegue con Docker

### 1️⃣ Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY bedrock-mcp-backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY bedrock-mcp-backend/ .

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["python", "app.py"]
```

### 2️⃣ Docker Compose

```yaml
version: '3.8'

services:
  bedrock-mcp-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AWS_REGION=us-east-1
      - S3_BUCKET=controlwebinars2025
      - MCP_BASE_URL=https://mcp.danielingram.shop/bedrock/tool-use
      - USE_PRESIGNED_URLS=true
      - LOG_LEVEL=INFO
    volumes:
      - ~/.aws:/root/.aws:ro
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Opcional: MCP S3 Wrapper
  mcp-s3-wrapper:
    build:
      context: .
      dockerfile: Dockerfile.wrapper
    ports:
      - "8001:8001"
    environment:
      - AWS_REGION=us-east-1
      - S3_BUCKET=controlwebinars2025
      - ORIGINAL_MCP_URL=https://mcp.danielingram.shop/bedrock/tool-use
    volumes:
      - ~/.aws:/root/.aws:ro
    restart: unless-stopped
    depends_on:
      - bedrock-mcp-backend
```

### 3️⃣ Construir y Ejecutar

```bash
# Construir imagen
docker build -t bedrock-mcp-backend .

# Ejecutar con compose
docker-compose up -d

# Verificar logs
docker-compose logs -f bedrock-mcp-backend
```

## ☁️ Despliegue en AWS

### 1️⃣ ECS con Fargate

```json
{
  "family": "bedrock-mcp-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "bedrock-mcp-backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/bedrock-mcp-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "AWS_REGION", "value": "us-east-1"},
        {"name": "S3_BUCKET", "value": "controlwebinars2025"},
        {"name": "MCP_BASE_URL", "value": "https://mcp.danielingram.shop/bedrock/tool-use"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/bedrock-mcp-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 2️⃣ Application Load Balancer

```yaml
# ALB Target Group
TargetGroup:
  Type: AWS::ElasticLoadBalancingV2::TargetGroup
  Properties:
    Port: 8000
    Protocol: HTTP
    TargetType: ip
    VpcId: !Ref VPC
    HealthCheckPath: /health
    HealthCheckIntervalSeconds: 30
    HealthyThresholdCount: 2
    UnhealthyThresholdCount: 5

# ALB Listener Rule
ListenerRule:
  Type: AWS::ElasticLoadBalancingV2::ListenerRule
  Properties:
    Actions:
      - Type: forward
        TargetGroupArn: !Ref TargetGroup
    Conditions:
      - Field: path-pattern
        Values: ["/bedrock/*", "/health", "/"]
    ListenerArn: !Ref Listener
    Priority: 100
```

### 3️⃣ Auto Scaling

```yaml
# ECS Service
Service:
  Type: AWS::ECS::Service
  Properties:
    Cluster: !Ref Cluster
    TaskDefinition: !Ref TaskDefinition
    DesiredCount: 2
    LaunchType: FARGATE
    NetworkConfiguration:
      AwsvpcConfiguration:
        SecurityGroups: [!Ref SecurityGroup]
        Subnets: [!Ref PrivateSubnet1, !Ref PrivateSubnet2]

# Auto Scaling Target
ScalingTarget:
  Type: AWS::ApplicationAutoScaling::ScalableTarget
  Properties:
    MaxCapacity: 10
    MinCapacity: 2
    ResourceId: !Sub service/${Cluster}/${Service.Name}
    RoleARN: !Sub arn:aws:iam::${AWS::AccountId}:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService
    ScalableDimension: ecs:service:DesiredCount
    ServiceNamespace: ecs

# Scaling Policy
ScalingPolicy:
  Type: AWS::ApplicationAutoScaling::ScalingPolicy
  Properties:
    PolicyName: cpu-scaling
    PolicyType: TargetTrackingScaling
    ScalingTargetId: !Ref ScalingTarget
    TargetTrackingScalingPolicyConfiguration:
      PredefinedMetricSpecification:
        PredefinedMetricType: ECSServiceAverageCPUUtilization
      TargetValue: 70
```

## 🔐 Configuración de Seguridad

### 1️⃣ IAM Role para ECS Task

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::controlwebinars2025/arquitecturas/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 2️⃣ Security Group

```yaml
SecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: Bedrock MCP Backend Security Group
    VpcId: !Ref VPC
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 8000
        ToPort: 8000
        SourceSecurityGroupId: !Ref ALBSecurityGroup
    SecurityGroupEgress:
      - IpProtocol: tcp
        FromPort: 443
        ToPort: 443
        CidrIp: 0.0.0.0/0
      - IpProtocol: tcp
        FromPort: 80
        ToPort: 80
        CidrIp: 0.0.0.0/0
```

## 📊 Monitoreo

### 1️⃣ CloudWatch Logs

```bash
# Crear log group
aws logs create-log-group --log-group-name /ecs/bedrock-mcp-backend

# Ver logs en tiempo real
aws logs tail /ecs/bedrock-mcp-backend --follow
```

### 2️⃣ CloudWatch Metrics

```yaml
# Custom Metrics
RequestCountMetric:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: bedrock-mcp-backend-request-count
    ComparisonOperator: GreaterThanThreshold
    EvaluationPeriods: 2
    MetricName: RequestCount
    Namespace: AWS/ApplicationELB
    Period: 300
    Statistic: Sum
    Threshold: 1000
    ActionsEnabled: true
    AlarmActions: [!Ref SNSTopic]

ErrorRateMetric:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: bedrock-mcp-backend-error-rate
    ComparisonOperator: GreaterThanThreshold
    EvaluationPeriods: 2
    MetricName: HTTPCode_Target_5XX_Count
    Namespace: AWS/ApplicationELB
    Period: 300
    Statistic: Sum
    Threshold: 10
    ActionsEnabled: true
    AlarmActions: [!Ref SNSTopic]
```

## 🔄 CI/CD Pipeline

### 1️⃣ GitHub Actions

```yaml
name: Deploy Bedrock MCP Backend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to ECR
        run: aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
      
      - name: Build and push image
        run: |
          docker build -t bedrock-mcp-backend .
          docker tag bedrock-mcp-backend:latest $ECR_REGISTRY/bedrock-mcp-backend:latest
          docker push $ECR_REGISTRY/bedrock-mcp-backend:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service --cluster production --service bedrock-mcp-backend --force-new-deployment
```

## 🧪 Testing

### 1️⃣ Health Check

```bash
curl -X GET http://localhost:8000/health
# Esperado: {"status":"healthy","service":"bedrock-mcp-backend"}
```

### 2️⃣ Tool Use Test

```bash
curl -X POST http://localhost:8000/bedrock/tool-use \
  -H "Content-Type: application/json" \
  -d '{
    "toolUse": {
      "toolUseId": "test-123",
      "name": "generate_diagram",
      "input": {
        "code": "from diagrams import Diagram\nfrom diagrams.aws import general\n\nwith Diagram(\"Test\", show=False):\n    user = general.User(\"Test\")",
        "project_name": "test-project"
      }
    }
  }'
```

### 3️⃣ Load Testing

```bash
# Instalar artillery
npm install -g artillery

# Crear test config
cat > load-test.yml << EOF
config:
  target: 'http://localhost:8000'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "Health check"
    requests:
      - get:
          url: "/health"
EOF

# Ejecutar test
artillery run load-test.yml
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **Error de conexión MCP**
   ```bash
   # Verificar conectividad
   curl -X GET https://mcp.danielingram.shop/health
   ```

2. **Error de permisos S3**
   ```bash
   # Verificar permisos IAM
   aws sts get-caller-identity
   aws s3 ls s3://controlwebinars2025/arquitecturas/
   ```

3. **Error de memoria**
   ```bash
   # Aumentar memoria en ECS task definition
   "memory": "2048"
   ```

### Logs Útiles

```bash
# Ver logs del contenedor
docker logs bedrock-mcp-backend

# Ver logs de ECS
aws logs tail /ecs/bedrock-mcp-backend --follow

# Ver métricas
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=bedrock-mcp-backend \
  --start-time 2025-07-29T00:00:00Z \
  --end-time 2025-07-29T23:59:59Z \
  --period 300 \
  --statistics Average
```
