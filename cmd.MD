# 1. Build the images
docker compose build

# 2. Start the services
docker compose up -d

# 3. Wait a bit for services to start
sleep 10

# 4. Test everything
./test_services.sh

# Show Docker services and ports
docker compose ps

# Show running containers
docker ps

# Show specific ports
lsof -i :3000,8000,5432

# Stop all containers
docker compose down -v

# Remove any orphaned containers
docker container prune -f

# Remove any unused networks
docker network prune -f

# Check if anything is still running
docker ps -a