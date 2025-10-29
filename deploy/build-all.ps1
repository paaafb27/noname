# build-all.ps1 - Docker v2 방식 빌드 스크립트
# 위치: F:\scandeals-crawler\deploy\build-all.ps1

$ErrorActionPreference = "Stop"
$ACCOUNT_ID = "127679825681"
$REGION = "ap-northeast-2"
$REPO_NAME = "scandeals-crawler"
$SITES = @("ppomppu", "ruliweb", "quasarzone", "arcalive", "eomisae", "fmkorea")

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "🚀 Docker v2 방식 빌드 & ECR 푸시" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# CRITICAL: DOCKER_BUILDKIT=0 강제
$env:DOCKER_BUILDKIT = "0"
Write-Host "✅ DOCKER_BUILDKIT=0 설정 완료`n" -ForegroundColor Green

# ECR 로그인
Write-Host "📌 ECR 로그인..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ECR 로그인 실패!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ ECR 로그인 완료`n" -ForegroundColor Green

# 프로젝트 루트로 이동
Set-Location "F:\scandeals-crawler"
Write-Host "📂 작업 디렉토리: $(Get-Location)`n" -ForegroundColor White

$totalStart = Get-Date
$successCount = 0

foreach ($site in $SITES) {
    Write-Host "`n──────────────────────────────────────" -ForegroundColor Gray
    Write-Host "[$site] 빌드 시작..." -ForegroundColor Cyan
    Write-Host "──────────────────────────────────────" -ForegroundColor Gray

    $IMAGE_URI = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${site}-latest"

    try {
        # Docker v2 방식 빌드 (buildx 사용 안 함!)
        Write-Host "  [1/2] Docker 빌드 중..." -ForegroundColor White

        docker build `
            --platform linux/amd64 `
            -t $IMAGE_URI `
            -f "functions/$site/Dockerfile" `
            .

        if ($LASTEXITCODE -ne 0) {
            throw "Docker 빌드 실패"
        }

        Write-Host "  ✅ 빌드 완료" -ForegroundColor Green

        # ECR 푸시
        Write-Host "  [2/2] ECR 푸시 중..." -ForegroundColor White

        docker push $IMAGE_URI

        if ($LASTEXITCODE -ne 0) {
            throw "ECR 푸시 실패"
        }

        Write-Host "  ✅ 푸시 완료`n" -ForegroundColor Green
        $successCount++

    } catch {
        Write-Host "  ❌ 실패: $_`n" -ForegroundColor Red
    }
}

# 원래 디렉토리로 복귀
Set-Location "F:\scandeals-crawler\deploy"

$totalDuration = ((Get-Date) - $totalStart).TotalMinutes

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "📊 최종 결과" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "✅ 성공: $successCount / 6" -ForegroundColor Green
Write-Host "⏱️  소요 시간: $([math]::Round($totalDuration, 1))분" -ForegroundColor White
Write-Host "================================================================`n" -ForegroundColor Cyan

if ($successCount -eq 6) {
    Write-Host "🎉 모든 이미지 빌드 & 푸시 완료!" -ForegroundColor Green
    Write-Host "`n다음 단계: .\update-all-lambda.ps1 실행`n" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  일부 이미지 빌드 실패" -ForegroundColor Yellow
}