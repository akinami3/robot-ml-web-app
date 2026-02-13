# Production Deployment Guide

## Production Compose

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Key Differences from Development

| Aspect | Development | Production |
|--------|------------|------------|
| Frontend | Vite dev server | nginx static |
| Backend | uvicorn --reload | gunicorn + uvicorn workers |
| Gateway | air (hot reload) | compiled binary |
| Ports | All exposed | Minimal (80, 443) |
| Resources | Unlimited | cgroup limits set |
| Logs | Console | JSON structured |

## Resource Limits (docker-compose.prod.yml)

| Service | CPU | Memory |
|---------|-----|--------|
| Frontend | 0.5 | 256MB |
| Backend | 2.0 | 1GB |
| Gateway | 1.0 | 512MB |
| PostgreSQL | 2.0 | 2GB |
| Redis | 0.5 | 512MB |
| Ollama | 4.0 | 8GB |

## PostgreSQL Tuning

```yaml
command: >
  -c shared_buffers=512MB
  -c effective_cache_size=1536MB
  -c work_mem=16MB
  -c maintenance_work_mem=128MB
  -c max_connections=100
```

## Health Checks

All services have health checks:

- **Frontend**: `wget --spider http://localhost/`
- **Backend**: `GET /health` → 200
- **Gateway**: TCP check on :8080
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`

## Security Checklist

- [ ] Generate strong JWT secret / RSA keys
- [ ] Change default database passwords
- [ ] Set `CORS_ORIGINS` to your domain
- [ ] Enable HTTPS (reverse proxy / Let's Encrypt)
- [ ] Review resource limits
- [ ] Set up database backups
- [ ] Configure log rotation

## Future Enhancements (Design Doc Only)

These items are planned but not yet implemented:

- **Observability**: Prometheus metrics, Grafana dashboards, Jaeger tracing
- **Kubernetes**: Helm charts for K8s deployment
- **Load Testing**: Locust / k6 performance benchmarks
- **GDPR**: Data retention policies, user data export/deletion
- **i18n**: Multi-language support (ja, en)
