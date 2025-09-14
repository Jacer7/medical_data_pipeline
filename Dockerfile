# Multi-stage Dockerfile for Medical Data Pipeline
# This single file creates all the different service images

# ==============================================
# Base Stage - Common dependencies
# ==============================================
FROM python:3.11-slim as base

# Metadata
LABEL maintainer="Medical Data Pipeline Team"
LABEL description="Medical publication data processing pipeline"

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build essentials
    gcc \
    g++ \
    make \
    # Network tools
    curl \
    wget \
    # Version control
    git \
    # Database client
    postgresql-client \
    # Text processing
    libpq-dev \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy and install base requirements first (for better Docker layer caching)
COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --upgrade pip && \
    pip install -r requirements/base.txt

# ==============================================
# Dagster Stage - Pipeline orchestration
# ==============================================
FROM base as dagster

# Install Dagster-specific dependencies
COPY requirements/dagster.txt /app/requirements/dagster.txt
RUN pip install -r requirements/dagster.txt

# Create Dagster-specific directories
RUN mkdir -p /opt/dagster/dagster_home \
             /opt/dagster/app \
             /opt/dagster/data \
             /opt/dagster/output \
             /opt/dagster/logs

# Copy Dagster configuration files
COPY dagster_home/ /opt/dagster/dagster_home/

# Copy source code
COPY src/ /opt/dagster/app/

# Set Dagster-specific environment variables
ENV DAGSTER_HOME=/opt/dagster/dagster_home
ENV PYTHONPATH="/opt/dagster/app:${PYTHONPATH}"

# Change ownership to non-root user
RUN chown -R appuser:appuser /opt/dagster

# Switch to non-root user
USER appuser

# Expose Dagster webserver port
EXPOSE 3000

# Health check for Dagster
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/server_info || exit 1

# Default command (will be overridden in docker-compose)
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]

# ==============================================
# Pipeline Stage - Main data processing
# ==============================================
FROM base as pipeline

# Install pipeline-specific dependencies
COPY requirements/pipeline.txt /app/requirements/pipeline.txt
RUN pip install -r requirements/pipeline.txt

# Create application directories
RUN mkdir -p /app/data/raw \
             /app/data/processed \
             /app/output \
             /app/logs \
             /app/temp

# Copy source code
COPY src/ /app/src/

# Copy initial data directory structure
COPY data/ /app/data/

# Set environment variables
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV DATA_DIR=/app/data
ENV OUTPUT_DIR=/app/output
ENV LOG_DIR=/app/logs

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user  
USER appuser

# Health check for pipeline worker
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "-m", "src.main"]

# ==============================================
# Analytics Stage - FastAPI service
# ==============================================
FROM base as analytics

# Install analytics-specific dependencies
COPY requirements/analytics.txt /app/requirements/analytics.txt
RUN pip install -r requirements/analytics.txt

# Create analytics directories
RUN mkdir -p /app/output \
             /app/logs \
             /app/temp

# Copy analytics source code
COPY analytics/ /app/

# Set environment variables
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV OUTPUT_DIR=/app/output

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==============================================
# Jupyter Stage - Data exploration
# ==============================================
FROM jupyter/scipy-notebook:latest as jupyter

# Switch to root for package installation
USER root

# Update and install system packages
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python packages
RUN pip install --no-cache-dir \
    # Dagster integration
    dagster==1.5.13 \
    dagster-postgres==0.21.13 \
    # Database
    psycopg2-binary==2.9.9 \
    sqlalchemy==2.0.23 \
    # Cloud storage
    boto3==1.34.4 \
    minio==7.2.0 \
    # Caching
    redis==5.0.1 \
    # Web framework
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    # Data science
    pandas==2.1.4 \
    numpy==1.25.2 \
    matplotlib==3.8.2 \
    seaborn==0.13.0 \
    plotly==5.17.0 \
    # Graph analysis
    networkx==3.2.1 \
    # Text processing
    nltk==3.8.1 \
    # Additional tools
    python-dotenv==1.0.0 \
    loguru==0.7.2

# Create work directories
RUN mkdir -p /home/jovyan/work/notebooks \
             /home/jovyan/work/data \
             /home/jovyan/work/output \
             /home/jovyan/work/logs

# Change ownership to jovyan user
RUN chown -R jovyan:users /home/jovyan/work

# Switch back to jovyan user
USER jovyan

# Set working directory
WORKDIR /home/jovyan/work

# Expose Jupyter port
EXPOSE 8888

# Health check for Jupyter
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8888/api || exit 1

# Default command
CMD ["start-notebook.sh", "--NotebookApp.token=medical_pipeline_token", "--NotebookApp.allow_root=True"]

# ==============================================
# Testing Stage - For running tests
# ==============================================
FROM base as testing

# Install testing dependencies
COPY requirements/testing.txt /app/requirements/testing.txt
RUN pip install -r requirements/testing.txt

# Create test directories
RUN mkdir -p /app/test-reports \
             /app/coverage-reports

# Copy all source code for testing
COPY src/ /app/src/
COPY analytics/ /app/analytics/
COPY tests/ /app/tests/

# Set environment variables
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTEST_OPTS="-v --tb=short"

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Default command for testing
CMD ["pytest", "tests/", "-v", "--cov=src", "--cov=analytics", "--cov-report=html:/app/coverage-reports/", "--junitxml=/app/test-reports/junit.xml"]

# ==============================================
# Production Stage - Optimized for deployment
# ==============================================
FROM base as production

# Install production dependencies only
COPY requirements/production.txt /app/requirements/production.txt
RUN pip install -r requirements/production.txt

# Create production directories
RUN mkdir -p /app/src \
             /app/analytics \
             /app/output \
             /app/logs

# Copy only necessary files for production
COPY src/ /app/src/
COPY analytics/ /app/analytics/

# Set production environment variables
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Production health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command (using gunicorn for better performance)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "analytics.api:app"]