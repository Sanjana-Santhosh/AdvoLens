#!/bin/bash

# ============================================
# AdvoLens - VPS Management Commands
# ============================================

CONTAINER_NAME="${CONTAINER_NAME:-advolens-backend}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo -e "${BLUE}AdvoLens VPS Management Commands${NC}"
    echo ""
    echo "Usage: ./vps-commands.sh <command>"
    echo ""
    echo "Commands:"
    echo "  seed          - Seed database with admin users and sample data"
    echo "  create-admin  - Create a single admin user interactively"
    echo "  shell         - Open Python shell inside container"
    echo "  bash          - Open bash shell inside container"
    echo "  logs          - View container logs"
    echo "  migrate       - Run database migrations"
    echo "  restart       - Restart the container"
    echo "  status        - Check container status"
    echo ""
}

case "$1" in
    seed)
        echo -e "${YELLOW}🌱 Seeding database...${NC}"
        docker exec -it $CONTAINER_NAME python -m app.scripts.seed_data
        ;;
    
    create-admin)
        echo -e "${YELLOW}👤 Creating admin user...${NC}"
        docker exec -it $CONTAINER_NAME python -m app.scripts.create_admin
        ;;
    
    shell)
        echo -e "${YELLOW}🐍 Opening Python shell...${NC}"
        docker exec -it $CONTAINER_NAME python
        ;;
    
    bash)
        echo -e "${YELLOW}💻 Opening bash shell...${NC}"
        docker exec -it $CONTAINER_NAME bash
        ;;
    
    logs)
        echo -e "${YELLOW}📜 Viewing logs...${NC}"
        docker logs -f $CONTAINER_NAME
        ;;
    
    migrate)
        echo -e "${YELLOW}🔄 Running migrations...${NC}"
        docker exec -it $CONTAINER_NAME alembic upgrade head
        ;;
    
    restart)
        echo -e "${YELLOW}🔄 Restarting container...${NC}"
        docker restart $CONTAINER_NAME
        ;;
    
    status)
        echo -e "${YELLOW}📊 Container status:${NC}"
        docker ps -f name=$CONTAINER_NAME
        ;;
    
    *)
        show_help
        ;;
esac
