#!/bin/bash
# test_services.sh - Simple script to test all services

echo "Medical Data Pipeline - Service Test"
echo "===================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to test if a port is responding
test_port() {
    local port=$1
    local service=$2
    echo -n "Testing $service (port $port): "
    
    if curl -s -f "http://localhost:$port" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}FAIL${NC}"
    fi
}

# Function to test if a port is listening
check_port() {
    local port=$1
    local service=$2
    echo -n "Checking $service (port $port): "
    
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}LISTENING${NC}"
    else
        echo -e "${RED}NOT LISTENING${NC}"
    fi
}

echo ""
echo -e "${BLUE}Service Status:${NC}"
docker compose ps

echo ""
echo -e "${BLUE}Port Check:${NC}"
check_port 3000 "Dagster"
check_port 8000 "FastAPI"
check_port 5432 "PostgreSQL"
check_port 6379 "Redis"
check_port 8888 "Jupyter"
check_port 9000 "MinIO API"
check_port 9001 "MinIO Console"

echo ""
echo -e "${BLUE}HTTP Health Check:${NC}"
test_port 8000 "FastAPI"

# Test specific endpoints
echo ""
echo -e "${BLUE}API Tests:${NC}"
echo -n "FastAPI Health: "
if curl -s "http://localhost:8000/health" | grep -q "healthy" 2>/dev/null; then
    echo -e "${GREEN}HEALTHY${NC}"
else
    echo -e "${RED}UNHEALTHY${NC}"
fi

echo -n "FastAPI Root: "
if curl -s "http://localhost:8000/" | grep -q "Analytics" 2>/dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

echo ""
echo -e "${BLUE}Database Tests:${NC}"
echo -n "PostgreSQL: "
if docker compose exec -T postgres pg_isready -U pipeline_user -d medical_pipeline > /dev/null 2>&1; then
    echo -e "${GREEN}READY${NC}"
else
    echo -e "${RED}NOT READY${NC}"
fi

echo -n "Redis: "
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "  Dagster UI:     http://localhost:3000"
echo "  FastAPI Docs:   http://localhost:8000/docs"
echo "  FastAPI Health: http://localhost:8000/health"
echo "  Jupyter:        http://localhost:8888?token=medical_pipeline_token"
echo "  MinIO Console:  http://localhost:9001 (admin/minioadmin123)"

echo ""
echo -e "${BLUE}Quick Commands:${NC}"
echo "  docker compose ps              # Show service status"
echo "  docker compose logs -f         # Show all logs"
echo "  docker compose logs dagster    # Show Dagster logs"
echo "  docker compose down            # Stop all services"
echo ""
echo "Test completed!"