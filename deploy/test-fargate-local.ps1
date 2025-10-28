# ==========================================
# Fargate 크롤러 로컬 Docker 테스트 스크립트
# ==========================================

$SITES = @("ppomppu", "fmkorea", "quasarzone", "arcalive", "eomisae", "ruliweb")

# 환경변수 설정
$API_URL = "https://scandeals.net/api/crawl/data"  # 실제 도메인
$API_KEY = "test-key-for-development-only"  # Spring Boot와 동일한 키

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Fargate 크롤러 로컬 테스트 시작" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "API URL: $API_URL" -ForegroundColor Cyan
Write-Host ""

# 프로젝트 루트로 이동
cd F:\scandeals-crawler

foreach ($site in $SITES) {
    Write-Host "[$site] 테스트 중..." -ForegroundColor Yellow
    
    # Docker 빌드 (프로젝트 루트에서 실행)
    docker build -t "scandeals-$site-test" `
        -f "functions/$site/Dockerfile" `
        .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[$site] ❌ 빌드 실패" -ForegroundColor Red
        continue
    }
    
    Write-Host "[$site] 빌드 성공, 실행 중..." -ForegroundColor Yellow
    
    # Docker 실행
    docker run --rm `
        -e API_URL=$API_URL `
        -e API_KEY=$API_KEY `
        -e FILTER_MINUTES=60 `
        "scandeals-$site-test"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[$site] ✅ 성공" -ForegroundColor Green
    } else {
        Write-Host "[$site] ❌ 실패" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  테스트 완료" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green