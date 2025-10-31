# deploy-complete.ps1 - 전체 배포 프로세스 통합
# 위치: F:\scandeals-crawler\deploy\deploy-complete.ps1

$ErrorActionPreference = "Continue"
$ACCOUNT_ID = "127679825681"
$REGION = "ap-northeast-2"
$REPO_NAME = "scandeals-crawler"
$ALL_SITES = @("ppomppu", "ruliweb", "quasarzone", "arcalive", "eomisae", "fmkorea")

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "🚀 전체 배포 프로세스" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# STEP 1: Lambda 함수 상태 확인
Write-Host "[1/4] Lambda 함수 상태 확인..." -ForegroundColor Yellow
$existingFunctions = @()
$missingFunctions = @()

foreach ($site in $ALL_SITES) {
    $check = aws lambda get-function --function-name "scandeals-$site" --region $REGION 2>&1
    if ($check -match "FunctionName") {
        $existingFunctions += $site
    } else {
        $missingFunctions += $site
    }
}

Write-Host "  ✅ 존재: $($existingFunctions -join ', ')" -ForegroundColor Green
if ($missingFunctions.Count -gt 0) {
    Write-Host "  ⚠️  없음: $($missingFunctions -join ', ')`n" -ForegroundColor Yellow
} else {
    Write-Host ""
}

# STEP 2: Lambda 함수 업데이트 (기존)
if ($existingFunctions.Count -gt 0) {
    Write-Host "[2/4] 기존 Lambda 함수 업데이트..." -ForegroundColor Yellow

    foreach ($site in $existingFunctions) {
        Write-Host "  [$site] 업데이트 중..." -ForegroundColor White
        $IMAGE_URI = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${site}-latest"

        aws lambda update-function-code `
            --function-name "scandeals-$site" `
            --image-uri $IMAGE_URI `
            --region $REGION `
            --output json | Out-Null

        aws lambda wait function-updated `
            --function-name "scandeals-$site" `
            --region $REGION 2>&1 | Out-Null

        Write-Host "  ✅ 완료" -ForegroundColor Green
    }
    Write-Host ""
}

# STEP 3: Lambda 함수 생성 (누락)
if ($missingFunctions.Count -gt 0) {
    Write-Host "[3/4] 누락된 Lambda 함수 생성..." -ForegroundColor Yellow
    $ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/lambda-crawler-role"

    foreach ($site in $missingFunctions) {
        Write-Host "  [$site] 생성 중..." -ForegroundColor White
        $IMAGE_URI = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${site}-latest"

        aws lambda create-function `
            --function-name "scandeals-$site" `
            --package-type Image `
            --code ImageUri=$IMAGE_URI `
            --role $ROLE_ARN `
            --timeout 900 `
            --memory-size 2048 `
            --environment "Variables={SPRING_BOOT_URL=http://3.36.72.54:3307,FILTER_MINUTES=60}" `
            --region $REGION `
            --output json | Out-Null

        Write-Host "  ✅ 완료" -ForegroundColor Green
    }
    Write-Host ""
} else {
    Write-Host "[3/4] 모든 Lambda 함수 존재 (생성 건너뜀)`n" -ForegroundColor Green
}

# STEP 4: Lambda 테스트 실행
Write-Host "[4/4] Lambda 함수 테스트 실행..." -ForegroundColor Yellow

$testSite = "ppomppu"
Write-Host "  [$testSite] 테스트 중..." -ForegroundColor White

$testResult = aws lambda invoke `
    --function-name "scandeals-$testSite" `
    --region $REGION `
    --log-type Tail `
    response.json 2>&1

if ($testResult -match "StatusCode") {
    $response = Get-Content response.json -Raw
    Write-Host "  응답: $response" -ForegroundColor White

    # 로그 확인
    $logs = aws lambda invoke `
        --function-name "scandeals-$testSite" `
        --region $REGION `
        --log-type Tail `
        --query 'LogResult' `
        --output text 2>&1

    if ($logs) {
        $decodedLogs = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($logs))
        Write-Host "`n  최근 로그:" -ForegroundColor Cyan
        $decodedLogs -split "`n" | Select-Object -Last 10 | ForEach-Object {
            Write-Host "    $_" -ForegroundColor Gray
        }
    }

    Write-Host "`n  ✅ 테스트 완료" -ForegroundColor Green
} else {
    Write-Host "  ❌ 테스트 실패: $testResult" -ForegroundColor Red
}

Remove-Item response.json -ErrorAction SilentlyContinue

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "🎉 전체 배포 완료!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan

Write-Host "`n다음 단계:" -ForegroundColor Yellow
Write-Host "  1. AWS Lambda 콘솔에서 각 함수 확인" -ForegroundColor White
Write-Host "  2. EventBridge 스케줄 설정 (자동 실행)" -ForegroundColor White
Write-Host "  3. CloudWatch 로그 모니터링`n" -ForegroundColor White