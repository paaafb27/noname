#!/bin/bash

##############################################
# Lambda 함수 로컬 테스트 스크립트
#
# 목적:
#   - AWS 배포 전 로컬에서 Lambda 테스트
#   - Playwright 동작 확인
#   - API 연동 테스트
#
# 사용법:
#   ./scripts/test-lambda-local.sh ppomppu
#
# 효과:
#   - 배포 전 버그 발견 가능
#   - 테스트 주기 10분 → 10초 단축
##############################################

set -e

if [ $# -ne 1 ]; then
    echo "사용법: ./scripts/test-lambda-local.sh <site>"
    echo "예시: ./scripts/test-lambda-local.sh ppomppu"
    exit 1
fi

SITE=$1
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Lambda 로컬 테스트: ${SITE}${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 환경변수 로드
source .env

# 2. Python 가상환경 설정
echo -e "${YELLOW}Step 1: Python 가상환경 설정${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 3. 의존성 설치
echo -e "${YELLOW}Step 2: 의존성 설치${NC}"
pip install -r lambda/scrapers/${SITE}/requirements.txt
pip install playwright
python -m playwright install chromium

# 4. Lambda 함수 실행
echo -e "${YELLOW}Step 3: Lambda 함수 실행${NC}"
cd lambda/scrapers/${SITE}

# 테스트 이벤트 생성
cat > test_event.json <<EOF
{
  "test": true,
  "api_url": "${SPRING_BOOT_API_URL}/api/crawl/data",
  "api_key": "${CRAWLER_API_KEY}"
}
EOF

# Lambda 함수 실행
python -c "
import json
from lambda_function import lambda_handler

with open('test_event.json', 'r') as f:
    event = json.load(f)

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"

# 정리
rm -f test_event.json
cd ../../..

echo ""
echo -e "${GREEN}✅ 로컬 테스트 완료!${NC}"
echo -e "${YELLOW}Spring Boot 로그를 확인하세요.${NC}"

deactivate