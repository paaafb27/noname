#!/bin/bash

##############################################
# Docker 컨테이너 시작 스크립트
#
# 목적:
#   - MySQL + Redis 컨테이너 시작
#   - 상태 확인 및 로그 출력
#
# 사용법:
#   ./scripts/start-docker.sh
##############################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Docker 컨테이너 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# Docker Compose 시작
docker-compose up -d

# 상태 확인
echo -e "${YELLOW}컨테이너 상태:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${GREEN}✅ Docker 컨테이너 시작 완료!${NC}"
echo ""
echo -e "${YELLOW}로그 확인:${NC}"
echo "   docker-compose logs -f mysql"
echo "   docker-compose logs -f redis"