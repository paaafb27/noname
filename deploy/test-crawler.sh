#!/bin/bash

###############################################################################
# 개별 크롤러 로컬 테스트 스크립트
# 
# 목적: 특정 크롤러를 Docker로 빌드하고 로컬에서 테스트
# 사용법: ./test-crawler.sh ppomppu
###############################################################################

set -e  # 에러 발생 시 즉시 중단

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###############################################################################
# 인자 확인
###############################################################################

if [ $# -lt 1 ]; then
    echo -e "${RED}사용법: $0 <crawler_name>${NC}"
    echo -e "${YELLOW}예시: $0 ppomppu${NC}"
    echo ""
    echo -e "사용 가능한 크롤러:"
    echo -e "  - ppomppu"
    echo -e "  - ruliweb"
    echo -e "  - fmkorea"
    echo -e "  - quasarzone"
    echo -e "  - arcalive"
    echo -e "  - eomisae"
    exit 1
fi

CRAWLER_NAME=$1
DOCKERFILE_PATH="functions/${CRAWLER_NAME}/Dockerfile"
IMAGE_TAG="${CRAWLER_NAME}-crawler:local"

# API 엔드포인트 설정 (기본값: localhost)
API_ENDPOINT="${API_ENDPOINT:-http://host.docker.internal:8080}"

# 필터링 시간 (기본값: 30분)
FILTER_MINUTES="${FILTER_MINUTES:-30}"

###############################################################################
# Dockerfile 존재 확인
###############################################################################

if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo -e "${RED}✗ Dockerfile 없음: ${DOCKERFILE_PATH}${NC}"
    exit 1
fi

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  ${CRAWLER_NAME} 크롤러 테스트${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "Dockerfile: ${YELLOW}${DOCKERFILE_PATH}${NC}"
echo -e "이미지 태그: ${YELLOW}${IMAGE_TAG}${NC}"
echo -e "API 엔드포인트: ${YELLOW}${API_ENDPOINT}${NC}"
echo -e "필터링 시간: ${YELLOW}${FILTER_MINUTES}분${NC}"
echo ""

###############################################################################
# 1. Docker 이미지 빌드
###############################################################################

echo -e "${YELLOW}🔨 [1/2] Docker 이미지 빌드 중...${NC}"
BUILD_START=$(date +%s)

if docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_TAG" .; then
    BUILD_END=$(date +%s)
    BUILD_TIME=$((BUILD_END - BUILD_START))
    echo -e "${GREEN}✓ 빌드 성공 (${BUILD_TIME}초)${NC}"
else
    echo -e "${RED}✗ 빌드 실패${NC}"
    exit 1
fi

echo ""

###############################################################################
# 2. Docker 컨테이너 실행
###############################################################################

echo -e "${YELLOW}🚀 [2/2] 크롤러 실행 중...${NC}"
echo ""

RUN_START=$(date +%s)

# Docker 실행 (타임아웃 180초)
if timeout 180 docker run --rm \
    -e API_ENDPOINT="${API_ENDPOINT}" \
    -e FILTER_MINUTES="${FILTER_MINUTES}" \
    "${IMAGE_TAG}"; then
    
    RUN_END=$(date +%s)
    RUN_TIME=$((RUN_END - RUN_START))
    
    echo ""
    echo -e "${GREEN}✓ 크롤러 실행 완료 (${RUN_TIME}초)${NC}"
    exit 0
else
    EXIT_CODE=$?
    RUN_END=$(date +%s)
    RUN_TIME=$((RUN_END - RUN_START))
    
    echo ""
    if [ $EXIT_CODE -eq 124 ]; then
        echo -e "${RED}✗ 타임아웃 (180초 초과)${NC}"
    else
        echo -e "${RED}✗ 실행 실패 (Exit Code: ${EXIT_CODE})${NC}"
    fi
    exit 1
fi
