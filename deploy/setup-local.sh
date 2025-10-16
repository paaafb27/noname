#!/bin/bash

##############################################
# 로컬 개발 환경 설정 스크립트
#
# 목적:
#   - 프로젝트 클론 후 최초 1회 실행
#   - 필요한 도구 설치 및 환경 설정
#   - Docker 컨테이너 자동 시작
#
# 사용법:
#   ./scripts/setup-local.sh
#
# 효과:
#   - 수동 설정 30분 → 자동 설정 3분
##############################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  scanDeals 로컬 환경 설정${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 필수 도구 확인
echo -e "${YELLOW}Step 1: 필수 도구 확인${NC}"

command -v docker >/dev/null 2>&1 || {
    echo -e "${RED}❌ Docker가 설치되지 않았습니다.${NC}"
    echo "설치: https://docs.docker.com/get-docker/"
    exit 1
}
echo "✅ Docker 설치됨"

command -v docker-compose >/dev/null 2>&1 || {
    echo -e "${RED}❌ Docker Compose가 설치되지 않았습니다.${NC}"
    exit 1
}
echo "✅ Docker Compose 설치됨"

command -v java >/dev/null 2>&1 || {
    echo -e "${RED}❌ Java가 설치되지 않았습니다.${NC}"
    echo "설치: brew install openjdk@17"
    exit 1
}
echo "✅ Java 설치됨"

# 2. 환경변수 파일 생성
echo -e "${YELLOW}Step 2: 환경변수 파일 생성${NC}"

if [ ! -f .env ]; then
    cat > .env <<EOF
# MySQL
MYSQL_USER=scandeals
MYSQL_PASSWORD=scandeals09123
MYSQL_DATABASE=scandeals
MYSQL_PORT=3307

# Redis
REDIS_PASSWORD=redis1234
REDIS_PORT=6379

# JWT
JWT_SECRET=scandeals-super-secret-key-minimum-32-characters-required-2024

# Spring Boot
SPRING_PROFILES_ACTIVE=local
JPA_DDL_AUTO=update
SHOW_SQL=true

# AWS (배포 시 필요)
AWS_REGION=ap-northeast-2
SPRING_BOOT_API_URL=http://localhost:8080
CRAWLER_API_KEY=dev-secret-key

# OAuth (Google Console에서 발급)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
EOF
    echo "✅ .env 파일 생성됨 (OAuth 키는 직접 입력하세요)"
else
    echo "✅ .env 파일 이미 존재"
fi

# 3. Docker 컨테이너 시작
echo -e "${YELLOW}Step 3: Docker 컨테이너 시작${NC}"
docker-compose up -d

# 4. 컨테이너 상태 확인
echo -e "${YELLOW}Step 4: 컨테이너 상태 확인 (10초 대기)${NC}"
sleep 10

docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 5. MySQL 연결 테스트
echo -e "${YELLOW}Step 5: MySQL 연결 테스트${NC}"
docker exec -it scandeals-mysql mysql -uscandeals -pscandeals09123 -e "SELECT 'MySQL OK' AS status;" 2>/dev/null && \
    echo "✅ MySQL 연결 성공" || \
    echo -e "${RED}❌ MySQL 연결 실패${NC}"

# 6. Redis 연결 테스트
echo -e "${YELLOW}Step 6: Redis 연결 테스트${NC}"
docker exec -it scandeals-redis redis-cli -a redis1234 PING 2>/dev/null && \
    echo "✅ Redis 연결 성공" || \
    echo -e "${RED}❌ Redis 연결 실패${NC}"

# 7. Gradle 빌드 (Spring Boot 의존성 다운로드)
echo -e "${YELLOW}Step 7: Gradle 빌드${NC}"
./gradlew clean build -x test

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 로컬 환경 설정 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "1. .env 파일에서 GOOGLE_CLIENT_ID/SECRET 입력"
echo "2. Spring Boot 실행: ./gradlew bootRun"
echo "3. 접속: http://localhost:8080"
echo ""
echo -e "${YELLOW}Lambda 로컬 테스트:${NC}"
echo "   ./scripts/test-lambda-local.sh ppomppu"