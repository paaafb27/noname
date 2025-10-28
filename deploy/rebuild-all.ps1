# rebuild-all.ps1
# 위치: F:\scandeals-crawler\deploy\rebuild-all.ps1

$ErrorActionPreference = "Continue"
$REGION = "ap-northeast-2"
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$REPOSITORY = "scandeals-crawler"
$ECR_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY"
$SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")

# deploy 디렉토리에서 프로젝트 루트로 이동
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "🚀 전체 사이트 재배포" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan
Write-Host "📂 작업 디렉토리: $projectRoot`n" -ForegroundColor White

# buildx 빌더 생성 (한 번만 실행)
Write-Host "🔧 Docker buildx 설정..." -ForegroundColor Yellow
docker buildx create --name multiarch --use 2>&1 | Out-Null
docker buildx inspect --bootstrap 2>&1 | Out-Null
Write-Host "✅ buildx 준비 완료`n" -ForegroundColor Green

# ECR 로그인
Write-Host "📌 ECR 로그인..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI | Out-Null
Write-Host "✅ 로그인 완료`n" -ForegroundColor Green

$totalStart = Get-Date
$successCount = 0

foreach ($site in $SITES) {
    Write-Host "`n[$site] 시작..." -ForegroundColor Yellow

    try {
        # buildx로 빌드 및 푸시 (한 번에)
        Write-Host "  [1/2] 빌드 & 푸시 (linux/amd64)..." -ForegroundColor White
        docker buildx build `
            --platform linux/amd64 `
            --provenance=false `
            --sbom=false `
            -t ${ECR_URI}:${site}-latest `
            -f functions/$site/Dockerfile `
            --push `
            .

        if ($LASTEXITCODE -ne 0) { throw "빌드/푸시 실패" }
        Write-Host "  ✅ 빌드 & 푸시 완료" -ForegroundColor Green

        # Lambda 업데이트
        Write-Host "  [2/2] Lambda 업데이트..." -ForegroundColor White
        aws lambda update-function-code `
            --function-name "scandeals-$site" `
            --image-uri "${ECR_URI}:${site}-latest" `
            --region $REGION | Out-Null

        aws lambda wait function-updated --function-name "scandeals-$site" --region $REGION 2>&1 | Out-Null
        Write-Host "  ✅ 완료" -ForegroundColor Green

        $successCount++

    } catch {
        Write-Host "  ❌ 실패: $_" -ForegroundColor Red
    }
}

$totalDuration = ((Get-Date) - $totalStart).TotalMinutes
Write-Host "`n✅ 완료: $successCount/6 ($([math]::Round($totalDuration, 1))분)`n" -ForegroundColor Cyan