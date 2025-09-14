# Medical Data Pipeline

Scalable data pipeline for processing medical publication data using **Dagster**, **FastAPI**, and **Docker**.

## Quick Start (Infrastructure Only)

This gets all services running with placeholder code to test the infrastructure.

### 1. Setup Project

```bash
# Run the setup script for SSH or HTTPS
git clone git@github.com:Jacer7/medical_data_pipeline.git
or 
git clone https://github.com/Jacer7/medical_data_pipeline.git
```

### 2. Start Infrastructure

```bash
# Build and start all services
docker-compose build
docker-compose up -d
```

### 3. Verify Everything is Working

```bash
# Check service status
make status

# Test all services
make test-services

# View logs
make logs
```

### 4. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **Dagster UI** | http://localhost:3000 | Pipeline orchestration & monitoring |
| **FastAPI Docs** | http://localhost:8000/docs | Auto-generated API documentation |
| **FastAPI Health** | http://localhost:8000/health | API health check |
| **Jupyter Lab** | http://localhost:8888?token=medical_pipeline_token | Data exploration |
| **MinIO Console** | http://localhost:9001 | Storage management (admin/minioadmin123) |
| **Dashboard** | http://localhost:8080 | Simple monitoring dashboard |

## Test Commands

```bash
# Test FastAPI
curl http://localhost:8000/health
curl http://localhost:8000/test

# Test PostgreSQL
docker-compose exec postgres psql -U pipeline_user -d medical_pipeline -c "SELECT * FROM medical_pipeline.health_check;"

# Test Redis
docker-compose exec redis redis-cli ping

# Test Dagster (should show sample assets)
# Visit: http://localhost:3000
```

## Project Structure

```
medical_data_pipeline/
├── docker-compose.yml         # Main orchestration
├── Dockerfile                 # Multi-stage build
├── Makefile                   # Common commands
├── requirements/              # Python dependencies
├── src/                       # Main pipeline code
├── analytics/                 # FastAPI ad-hoc queries
├── dagster_home/             # Dagster configuration
├── data/raw/                 # Input data files
├── output/                   # Pipeline outputs
├── notebooks/                # Jupyter notebooks
├── sql/init/                 # Database initialization
└── logs/                     # Application logs
```

## Services Overview

- **postgres**: Database for pipeline metadata
- **minio**: S3-compatible object storage  
- **redis**: Caching and task queuing
- **dagster**: Pipeline orchestration (UI + daemon)
- **pipeline_worker**: Main data processing
- **analytics_api**: FastAPI for ad-hoc queries
- **jupyter**: Data exploration environment

## Common Commands

```bash
# Development
make setup          # Initial setup
make up             # Start services
make down           # Stop services
make logs           # View logs
make status         # Check status

# Testing
make test-services  # Test all services
make test-api       # Test FastAPI endpoints

# Cleanup
make clean          # Remove containers and volumes
```

## Troubleshooting

### Services won't start:
```bash
# Check Docker resources
docker system df

# Check logs
docker-compose logs postgres
docker-compose logs dagster
```

### Port conflicts:
```bash
# Check what's using ports
lsof -i :3000
lsof -i :8000
lsof -i :5432
```

### Permission issues:
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

## Expected Results

### Successful Infrastructure Setup

When everything is working, you should see:

1. **Dagster UI** (localhost:3000): Shows sample assets
2. **FastAPI** (localhost:8000/docs): Shows API documentation
3. **All health checks pass**: Green status indicators
4. **No error logs**: Clean startup logs

### Next Steps

Once infrastructure is running:
1. Implement actual data processing logic
2. Add real Dagster assets for the pipeline
3. Create the medical graph JSON output  
4. Implement the ad-hoc query logic

## Architecture

```
Data Sources → Ingestion → Processing → Graph Builder → JSON Output
     ↓              ↓           ↓            ↓
PostgreSQL ←   MinIO    ←   Redis    ←   Dagster (orchestration)
     ↓
FastAPI (ad-hoc queries) + Jupyter (exploration)
```

##  Notes

- This is the **infrastructure setup only**
- Pipeline logic will be implemented in next steps
- All services use health checks for reliable startup
- Data persists in Docker volumes
- Ready for Kubernetes production deployment