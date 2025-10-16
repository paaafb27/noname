#!/bin/bash

##############################################
# Lambda 함수 배포 자동화 스크립트
#
# 목적:
#   - Lambda 함수 코드 수정 시 자동 배포
#   - 사이트별 함수 일괄 배포 지원
#   - 배포 후 자동 테스트 실행
#
# 사용법:
#   ./scripts/deploy-lambda.sh              # 전체 배포
#   ./scripts/deploy-lambda.sh ppomppu      # 특정 사이트만 배포
#
# 효과:
#   - 수동 배포 시간 10분 → 1분으로 단축
#   - 실수로 인한 배포 오류 방지
##############################################

set -e  # 에러 발생 시 즉시 종료

# 색상 코드 (시각적 피드백)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

# AWS 설정 (환경변수에서 읽기)
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
LAYER_ARN="${PLAYWRIGHT_LAYER_ARN}"

# 배포할 함수 목록
SITES=("ppomppu" "ruliweb" "arcalive" "eomisae" "fmkorea" "quasarzone")

# 특정 사이트만 배포하는 경우
if [ $# -eq 1 ]; then
    SITES=("$1")
    echo -e "${YELLOW}[INFO] $1 함수만 배포합니다.${NC}"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Lambda 함수 배포 시작${NC}"
echo -e "${GREEN}========================================${NC}"

for site in "${SITES[@]}"; do
    FUNCTION_NAME="scandeals-${site}"
    ZIP_FILE="lambda-${site}.zip"

    echo -e "${YELLOW}[${site}] 배포 시작...${NC}"

    # 1. 의존성 패키지 설치
    echo "[${site}] Step 1: 의존성 설치"
    cd lambda/scrapers/${site}
    pip install -r requirements.txt -t package/ --platform manylinux2014_x86_64 --only-binary=:all:

    # 2. ZIP 파일 생성
    echo "[${site}] Step 2: ZIP 파일 생성"
    cd package
    zip -r ../${ZIP_FILE} .
    cd ..
    zip -g ${ZIP_FILE} lambda_function.py

    # 3. Lambda 함수 업데이트
    echo "[${site}] Step 3: Lambda 함수 업데이트"
    aws lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --zip-file fileb://${ZIP_FILE} \
        --region ${AWS_REGION}

    # 4. Layer 연결 (Playwright)
    echo "[${site}] Step 4: Layer 연결"
    aws lambda update-function-configuration \
        --function-name ${FUNCTION_NAME} \
        --layers ${LAYER_ARN} \
        --region ${AWS_REGION}

    # 5. 환경변수 설정
    echo "[${site}] Step 5: 환경변수 설정"
    aws lambda update-function-configuration \
        --function-name ${FUNCTION_NAME} \
        --environment Variables="{
            SPRING_BOOT_API_URL=${SPRING_BOOT_API_URL},
            API_KEY=${CRAWLER_API_KEY}
        }" \
        --region ${AWS_REGION}

    # 6. 배포 완료 대기
    echo "[${site}] Step 6: 배포 완료 대기..."
    aws lambda wait function-updated \
        --function-name ${FUNCTION_NAME} \
        --region ${AWS_REGION}

    echo -e "${GREEN}[${site}] ✅ 배포 완료!${NC}"

    # 7. 테스트 실행 (선택)
    if [ "${SKIP_TEST}" != "true" ]; then
        echo "[${site}] Step 7: 테스트 실행"
        aws lambda invoke \
            --function-name ${FUNCTION_NAME} \
            --region ${AWS_REGION} \
            --payload '{"test": true}' \
            response.json

        cat response.json
        echo ""
    fi

    # 정리
    rm -rf package ${ZIP_FILE} response.json
    cd ../../..

    echo -e "${GREEN}========================================${NC}\n"
done

echo -e "${GREEN}🎉 모든 Lambda 함수 배포 완료!${NC}"
echo -e "${YELLOW}💡 EventBridge 스케줄러를 활성화하세요:${NC}"
echo "   aws events enable-rule --name scandeals-ppomppu-schedule"