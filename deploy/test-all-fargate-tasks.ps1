# ==========================================
# 전체 Fargate Task 수동 실행 및 테스트
# ==========================================

$REGION = "ap-northeast-2"
$CLUSTER = "scandeals-crawler-cluster"
$SITES = @("ppomppu", "fmkorea", "quasarzone", "arcalive", "eomisae", "ruliweb")


$SECURITY_GROUP = "sg-06b877fb23276fcbf"  # 실제 값으로 변경
$SUBNETS = "subnet-0cf0b2476d85e7adb,subnet-0bcb51270debe69d6,subnet-0d1bac072b236398b,subnet-04352f96229a481ac"

Write-Host "========================================" -ForegroundColor Green
Write-Host "  전체 Fargate Task 수동 실행" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

foreach ($site in $SITES) {
    Write-Host "[$site] Task 실행 중..." -ForegroundColor Yellow

    $result = aws ecs run-task `
        --cluster $CLUSTER `
        --task-definition "scandeals-$site" `
        --launch-type FARGATE `
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}" `
        --region $REGION 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[$site] ✅ 실행 성공" -ForegroundColor Green
    } else {
        Write-Host "[$site] ❌ 실행 실패" -ForegroundColor Red
        Write-Host $result -ForegroundColor Red
    }

    Write-Host ""
    Start-Sleep -Seconds 2
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  60초 후 로그 확인..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Start-Sleep -Seconds 60

foreach ($site in $SITES) {
    Write-Host "`n[$site] 최근 로그:" -ForegroundColor Yellow
    aws logs tail /ecs/scandeals-$site --since 5m --region $REGION
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  테스트 완료" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green