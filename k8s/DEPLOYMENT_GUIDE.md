# Temporal Deployment Guide

## Prerequisites

1. **Kubernetes Cluster** (v1.24+)
2. **Helm** (v3.0+)
3. **kubectl** configured
4. **PostgreSQL** database available

## Step 1: Create Namespaces

```bash
kubectl create namespace ve-saas
kubectl create namespace temporal
```

## Step 2: Install Temporal Server

### Add Temporal Helm Repository
```bash
helm repo add temporalio https://go.temporal.io/helm-charts
helm repo update
```

### Create Temporal Values File

Create `temporal-values.yaml`:

```yaml
server:
  replicaCount: 3
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi
  
  config:
    persistence:
      default:
        driver: "sql"
        sql:
          driver: "postgres"
          host: "postgres.ve-saas"
          port: 5432
          database: "temporal"
          user: "temporal"
          password: "${TEMPORAL_POSTGRES_PASSWORD}"
          maxConns: 20
          maxIdleConns: 20
      
      visibility:
        driver: "sql"
        sql:
          driver: "postgres"
          host: "postgres.ve-saas"
          port: 5432
          database: "temporal_visibility"
          user: "temporal"
          password: "${TEMPORAL_POSTGRES_PASSWORD}"
          maxConns: 10
          maxIdleConns: 10

cassandra:
  enabled: false

mysql:
  enabled: false

postgresql:
  enabled: false  # Using external PostgreSQL

prometheus:
  enabled: true
  nodeExporter:
    enabled: false

grafana:
  enabled: true
  adminPassword: "${GRAFANA_ADMIN_PASSWORD}"

elasticsearch:
  enabled: false
```

### Install Temporal
```bash
# Replace placeholders with actual values
export TEMPORAL_POSTGRES_PASSWORD="your-secure-password"
export GRAFANA_ADMIN_PASSWORD="your-grafana-password"

# Install
helm install temporal temporalio/temporal \
  --namespace temporal \
  --values temporal-values.yaml \
  --wait
```

### Verify Installation
```bash
kubectl get pods -n temporal
kubectl get svc -n temporal
```

Expected output:
```
NAME                                      READY   STATUS    RESTARTS   AGE
temporal-frontend-xxxxx                   1/1     Running   0          2m
temporal-history-xxxxx                    1/1     Running   0          2m
temporal-matching-xxxxx                   1/1     Running   0          2m
temporal-worker-xxxxx                     1/1     Running   0          2m
```

## Step 3: Create Temporal Namespace

```bash
# Port-forward to Temporal frontend
kubectl port-forward -n temporal svc/temporal-frontend 7233:7233 &

# Create namespace using tctl
tctl --namespace ve-saas namespace register \
  --description "VE SaaS Production Namespace" \
  --retention 30
```

## Step 4: Deploy Temporal UI

```bash
kubectl apply -f k8s/temporal-ui.yaml
```

### Access Temporal UI
```bash
# Port-forward
kubectl port-forward -n temporal svc/temporal-ui 8080:8080

# Open browser
open http://localhost:8080
```

## Step 5: Configure Secrets

### Create Secrets from Environment Variables
```bash
# Load environment variables
source .env.production

# Create secrets
envsubst < k8s/secrets.yaml | kubectl apply -f -
```

### Or Create Manually
```bash
kubectl create secret generic ve-secrets \
  --namespace ve-saas \
  --from-literal=supabase-url="${SUPABASE_URL}" \
  --from-literal=supabase-service-key="${SUPABASE_SERVICE_KEY}" \
  --from-literal=redis-url="redis://redis.ve-saas:6379" \
  --from-literal=centrifugo-api-key="${CENTRIFUGO_API_KEY}" \
  --from-literal=agent-gateway-api-key="${AGENT_GATEWAY_API_KEY}"
```

## Step 6: Deploy ConfigMaps

```bash
kubectl apply -f k8s/configmaps.yaml
```

## Step 7: Deploy Temporal Worker

```bash
# Build worker image
docker build -f backend/Dockerfile.worker -t ve-backend-worker:latest backend/

# Tag for registry
docker tag ve-backend-worker:latest your-registry/ve-backend-worker:latest

# Push to registry
docker push your-registry/ve-backend-worker:latest

# Update image in deployment
kubectl set image deployment/temporal-worker \
  worker=your-registry/ve-backend-worker:latest \
  -n ve-saas

# Or apply deployment
kubectl apply -f k8s/temporal-worker-deployment.yaml
```

### Verify Worker Deployment
```bash
kubectl get pods -n ve-saas -l app=temporal-worker
kubectl logs -n ve-saas -l app=temporal-worker --tail=50
```

Expected log output:
```
INFO:root:Connecting to Temporal Server at temporal-frontend.temporal:7233...
INFO:root:Connected to Temporal Server.
INFO:root:Starting Temporal Worker on queue 'campaign-queue'...
```

## Step 8: Verify Workflow Execution

### Submit Test Task
```bash
# Port-forward to backend API
kubectl port-forward -n ve-saas svc/ve-backend 8000:8000 &

# Submit task
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -d '{
    "customer_id": "test-customer",
    "title": "Test Temporal Workflow",
    "description": "Verify Temporal integration"
  }'
```

### Check Workflow in Temporal UI
1. Open http://localhost:8080
2. Navigate to "Workflows"
3. Filter by namespace: "ve-saas"
4. Look for workflow ID starting with "orchestrator-"

## Step 9: Monitor Workers

### Check Worker Health
```bash
kubectl get pods -n ve-saas -l app=temporal-worker
```

### View Worker Logs
```bash
kubectl logs -n ve-saas -l app=temporal-worker -f
```

### Check HPA Status
```bash
kubectl get hpa -n ve-saas temporal-worker-hpa
```

Expected output:
```
NAME                  REFERENCE                    TARGETS         MINPODS   MAXPODS   REPLICAS
temporal-worker-hpa   Deployment/temporal-worker   30%/70%         3         10        3
```

## Step 10: Configure Monitoring

### Prometheus Metrics
Temporal exports metrics to Prometheus automatically. Add scrape config:

```yaml
scrape_configs:
  - job_name: 'temporal'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - temporal
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: temporal.*
        action: keep
```

### OpenObserve Integration
```bash
# Update backend deployment to export Temporal metrics
kubectl set env deployment/ve-backend \
  -n ve-saas \
  OTEL_EXPORTER_OTLP_ENDPOINT=http://openobserve.observability:5080
```

## Troubleshooting

### Worker Not Connecting
```bash
# Check worker logs
kubectl logs -n ve-saas -l app=temporal-worker --tail=100

# Check Temporal frontend service
kubectl get svc -n temporal temporal-frontend

# Test connectivity
kubectl run -it --rm debug \
  --image=curlimages/curl \
  --restart=Never \
  -- curl -v temporal-frontend.temporal:7233
```

### Workflows Not Starting
```bash
# Check if namespace exists
tctl --namespace ve-saas namespace describe

# Check worker registration
# In Temporal UI: Workers tab

# Check task queue
# In Temporal UI: Task Queues tab
```

### Database Connection Issues
```bash
# Check PostgreSQL connectivity
kubectl run -it --rm psql-test \
  --image=postgres:15 \
  --restart=Never \
  -- psql -h postgres.ve-saas -U temporal -d temporal -c "SELECT 1"
```

## Rollback Procedure

### Rollback Worker Deployment
```bash
kubectl rollout undo deployment/temporal-worker -n ve-saas
```

### Rollback to Previous Version
```bash
kubectl rollout history deployment/temporal-worker -n ve-saas
kubectl rollout undo deployment/temporal-worker -n ve-saas --to-revision=2
```

### Emergency: Pause Workers
```bash
kubectl scale deployment/temporal-worker -n ve-saas --replicas=0
```

## Production Checklist

- [ ] PostgreSQL database created with proper schemas
- [ ] Temporal Server deployed and healthy
- [ ] Temporal namespace "ve-saas" created
- [ ] Secrets configured with production values
- [ ] ConfigMaps applied
- [ ] Worker image built and pushed to registry
- [ ] Worker deployment applied and healthy
- [ ] HPA configured and working
- [ ] Monitoring configured (Prometheus + OpenObserve)
- [ ] Temporal UI accessible
- [ ] Test workflow executed successfully
- [ ] Alerts configured for workflow failures
- [ ] Backup strategy in place
- [ ] Rollback procedure tested

## Next Steps

1. **Load Testing**: Run load tests with 10+ concurrent workflows
2. **Monitoring**: Set up dashboards in Grafana/OpenObserve
3. **Alerting**: Configure alerts for workflow failures
4. **Documentation**: Update runbooks with operational procedures
5. **Training**: Train team on Temporal UI and debugging
