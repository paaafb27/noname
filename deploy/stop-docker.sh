#!/bin/bash

##############################################
# Docker 컨테이너 중지 스크립트
#
# 목적:
#   - MySQL + Redis 컨테이너 중지
#   - 데이터는 볼륨에 유지됨 (삭제 안 함)
#
# 사용법:
#   ./scripts/stop-docker.sh
##############################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Docker 컨테이너 중지 중...${NC}"

# Docker Compose 중지
docker-compose down

echo -e "${GREEN}✅ Docker 컨테이너 중지 완료!${NC}"
echo ""
echo -e "${YELLOW}💡 데이터는 유지됩니다. 완전히 삭제하려면:${NC}"
echo "   docker-compose down -v  # 볼륨까지 삭제"