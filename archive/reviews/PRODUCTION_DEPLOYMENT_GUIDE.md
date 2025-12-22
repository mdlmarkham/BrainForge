# BrainForge Production Deployment Guide

This guide provides comprehensive instructions for deploying BrainForge in a production environment with all Phase 4 hardening features implemented.

## Overview

Phase 4 production hardening includes:
- **Data Encryption**: Field-level encryption for sensitive data
- **RBAC**: Role-Based Access Control with fine-grained permissions
- **Monitoring**: Comprehensive observability with structured logging
- **Performance**: Caching and query optimization
- **Containerization**: Production-ready Docker configuration
- **Backup**: Automated backup and recovery procedures
- **GDPR Compliance**: Data export and deletion endpoints

## Prerequisites

### System Requirements
- Docker and Docker Compose
- PostgreSQL 16+ with pgvector extension
- Redis 7+ for caching
- 2GB+ RAM, 2+ CPU cores

### Environment Variables

Create a `.env` file with the following required variables:

```bash
# Database
DATABASE_URL=postgresql://username:password@database:5432/brainforge
POSTGRES_DB=brainforge
POSTGRES_USER=brainforge
POSTGRES_PASSWORD=your_secure_password

# Security
SECRET_KEY=your-super-secret-jwt-key-change-in-production
ENCRYPTION_KEY=your-encryption-key-for-data-at-rest
JWT_EXPIRE_MINUTES=1440

# Redis
REDIS_URL=redis://redis:6379

# Application
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Backup
BACKUP_RETENTION_DAYS=7
BACKUP_ENABLED=true
```

## Deployment Steps

### 1. Clone and Setup

```bash
git clone <repository-url>
cd BrainForge
cp .env.example .env
# Edit .env with your production values
```

### 2. Start Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database with pgvector
- Redis for caching
- BrainForge API with 4 workers
- Backup service (daily at 2 AM)

### 3. Run Migrations

```bash
docker-compose run migrations
```

### 4. Verify Deployment

Check health status:
```bash
curl http://localhost:8000/health
```

## Production Configuration

### Security Hardening

#### Data Encryption
- Sensitive data encrypted at rest using Fernet encryption
- Encryption key managed via `ENCRYPTION_KEY` environment variable
- Key rotation supported via `KeyManagementService`

#### RBAC Implementation
- Four user roles: Admin, User, Read-Only, Guest
- Fine-grained permissions for all operations
- Permission middleware enforces access control

#### Rate Limiting
- Default: 100 requests/minute
- Authentication endpoints: 10 requests/minute
- File uploads: 5 requests/minute
- Search: 30 requests/minute

### Monitoring and Observability

#### Health Checks
- `/health` - Comprehensive system health
- `/readiness` - Kubernetes readiness probe
- `/liveness` - Kubernetes liveness probe

#### Metrics Endpoints
- `/api/v1/system/metrics` - System metrics (admin only)
- `/api/v1/system/metrics/research` - Research metrics
- Structured JSON logging for all operations

#### Performance Monitoring
- Request duration tracking
- Cache hit/miss statistics
- Database query performance

### Backup and Recovery

#### Automated Backups
- Daily backups at 2 AM
- 7-day retention policy
- Compressed backup files

#### Manual Backup Operations
```bash
# Create backup
docker-compose run backup python src/cli/backup.py create

# List backups
docker-compose run backup python src/cli/backup.py list

# Restore backup
docker-compose run backup python src/cli/backup.py restore /backups/brainforge_backup_20241201_020000.sql.gz
```

### GDPR Compliance

#### Data Export
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/gdpr/data-export
```

#### Data Deletion
```bash
curl -X DELETE -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/gdpr/data-deletion
```

## Scaling Considerations

### Horizontal Scaling
- Stateless API design supports multiple instances
- Redis shared cache for session consistency
- Database connection pooling configured

### Resource Limits
```yaml
# docker-compose.yml resource limits
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```

### Performance Optimization
- Redis caching for frequent queries
- Database query optimization
- Connection pooling (pool_size: 10, max_overflow: 20)

## Security Best Practices

### Network Security
- Use reverse proxy (nginx/Traefik) for SSL termination
- Configure firewall rules
- Enable CORS with specific allowed origins

### Database Security
- Use strong passwords
- Enable SSL connections
- Regular security updates

### Application Security
- Regular dependency updates
- Security headers configuration
- Input validation and sanitization

## Monitoring and Alerting

### Log Aggregation
- Structured JSON logs for easy parsing
- Integration with ELK stack or similar
- Log rotation and retention policies

### Metrics Collection
- Prometheus metrics endpoint (future enhancement)
- Custom performance metrics
- Alerting on critical thresholds

### Health Monitoring
- Automated health checks
- Alerting on service degradation
- Performance baseline monitoring

## Disaster Recovery

### Backup Strategy
- Daily automated backups
- Off-site backup storage
- Regular backup verification

### Recovery Procedures
1. Stop application services
2. Restore latest backup
3. Verify data integrity
4. Restart services

### High Availability
- Database replication (consider for critical deployments)
- Load balancer for API instances
- Geographic redundancy for critical components

## Maintenance Procedures

### Regular Maintenance
- Weekly security updates
- Monthly backup verification
- Quarterly performance review

### Update Procedures
1. Backup current deployment
2. Update code and dependencies
3. Run database migrations
4. Deploy new version
5. Verify functionality

### Troubleshooting
- Check application logs: `docker-compose logs api`
- Check database connectivity
- Verify environment configuration
- Monitor resource usage

## Compliance and Auditing

### GDPR Compliance
- Data export functionality
- Data deletion (anonymization)
- Consent management
- Data retention policies

### Audit Trail
- Comprehensive logging of all operations
- User action tracking
- Security event monitoring

## Support and Resources

### Documentation
- API documentation: `/docs`
- OpenAPI specification: `/openapi.json`

### Monitoring Tools
- Health endpoints for automated monitoring
- Metrics endpoints for performance tracking
- Log aggregation for troubleshooting

### Contact Information
- Support: team@brainforge.dev
- Documentation: https://brainforge.dev/docs
- Issues: GitHub repository issues

## Conclusion

BrainForge is now production-ready with comprehensive security, monitoring, and compliance features. Regular maintenance and monitoring will ensure optimal performance and security in your production environment.