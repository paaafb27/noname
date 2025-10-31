#!/bin/bash

###############################################################################
# 전체 크롤러 로컬 테스트 스크립트
# 
# 목적: 모든 크롤러를 Docker로 빌드하고 로컬에서 테스트
# 사용법: ./test-all-crawlers.sh
###############################################################################

set -e  # 에러 발생 시 즉시 중단

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API 엔드포인트 설정
API_ENDPOINT="${API_ENDPOINT:-http://host.docker.internal:8080}"

# 크롤러 목록 (디렉토리명)
CRAWLERS=(
    "ppomppu"
    "ruliweb"
    "fmkorea"
    "quasarzone"
    "arcalive"
    "eomisae"
)

# 결과 저장
SUCCESS_COUNT=0
FAIL_COUNT=0
FAILED_CRAWLERS=()

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  전체 크롤러 로컬 테스트 시작${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "API 엔드포인트: ${YELLOW}${API_ENDPOINT}${NC}"
echo -e "테스트 크롤러 수: ${YELLOW}${#CRAWLERS[@]}개${NC}"
echo ""

# 시작 시간 기록
START_TIME=$(date +%s)

###############################################################################
# 각 크롤러 테스트
###############################################################################

for CRAWLER in "${CRAWLERS[@]}"; do
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[$(date +%H:%M:%S)] 테스트 중: ${CRAWLER}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    DOCKERFILE_PATH="functions/${CRAWLER}/Dockerfile"
    IMAGE_TAG="${CRAWLER}-crawler:local"
    
    # 1. Dockerfile 존재 확인
    if [ ! -f "$DOCKERFILE_PATH" ]; then
        echo -e "${RED}✗ Dockerfile 없음: ${DOCKERFILE_PATH}${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED_CRAWLERS+=("${CRAWLER}")
        continue
    fi
    
    # 2. Docker 이미지 빌드
    echo -e "${YELLOW}🔨 Docker 이미지 빌드 중...${NC}"
    if docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_TAG" . > /tmp/${CRAWLER}_build.log 2>&1; then
        echo -e "${GREEN}✓ 빌드 성공${NC}"
    else
        echo -e "${RED}✗ 빌드 실패${NC}"
        echo -e "${RED}로그: /tmp/${CRAWLER}_build.log${NC}"
        tail -n 20 /tmp/${CRAWLER}_build.log
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED_CRAWLERS+=("${CRAWLER}")
        continue
    fi
    
    # 3. Docker 컨테이너 실행
    echo -e "${YELLOW}🚀 크롤러 실행 중...${NC}"
    if timeout 120 docker run --rm \
        -e API_ENDPOINT="${API_ENDPOINT}" \
        -e FILTER_MINUTES="30" \
        "${IMAGE_TAG}" > /tmp/${CRAWLER}_run.log 2>&1; then
        
        # 실행 결과 확인
        if grep -q "크롤링 완료" /tmp/${CRAWLER}_run.log || \
           grep -q "총.*개 수집" /tmp/${CRAWLER}_run.log; then
            echo -e "${GREEN}✓ 실행 성공${NC}"
            
            # 수집 개수 출력
            COLLECTED=$(grep -oP "총 \K\d+(?=개 수집)" /tmp/${CRAWLER}_run.log | tail -1)
            if [ -n "$COLLECTED" ]; then
                echo -e "${GREEN}  📊 수집 개수: ${COLLECTED}개${NC}"
            fi
            
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo -e "${RED}✗ 실행 실패 (예상 출력 없음)${NC}"
            echo -e "${RED}로그: /tmp/${CRAWLER}_run.log${NC}"
            tail -n 20 /tmp/${CRAWLER}_run.log
            FAIL_COUNT=$((FAIL_COUNT + 1))
            FAILED_CRAWLERS+=("${CRAWLER}")
        fi
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 124 ]; then
            echo -e "${RED}✗ 타임아웃 (120초 초과)${NC}"
        else
            echo -e "${RED}✗ 실행 실패 (Exit Code: ${EXIT_CODE})${NC}"
        fi
        echo -e "${RED}로그: /tmp/${CRAWLER}_run.log${NC}"
        tail -n 20 /tmp/${CRAWLER}_run.log
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED_CRAWLERS+=("${CRAWLER}")
    fi
    
    # 로그 파일 크기 확인
    LOG_SIZE=$(du -h /tmp/${CRAWLER}_run.log | cut -f1)
    echo -e "${BLUE}  📄 로그 크기: ${LOG_SIZE}${NC}"
done

###############################################################################
# 테스트 결과 요약
###############################################################################

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))

echo -e "\n${BLUE}=====================================${NC}"
echo -e "${BLUE}  테스트 결과 요약${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "전체 크롤러: ${YELLOW}${#CRAWLERS[@]}개${NC}"
echo -e "성공: ${GREEN}${SUCCESS_COUNT}개${NC}"
echo -e "실패: ${RED}${FAIL_COUNT}개${NC}"
echo -e "소요 시간: ${YELLOW}${DURATION_MIN}분 ${DURATION_SEC}초${NC}"
echo ""

if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}실패한 크롤러:${NC}"
    for FAILED in "${FAILED_CRAWLERS[@]}"; do
        echo -e "  ${RED}✗ ${FAILED}${NC}"
        echo -e "    로그: /tmp/${FAILED}_run.log"
    done
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ 모든 크롤러 테스트 성공!${NC}"
    echo ""
    exit 0
fi
