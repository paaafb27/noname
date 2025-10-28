# update-filter-time.ps1
$REGION = "ap-northeast-2"
$SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")

# 2시간 = 120분
$FILTER_MINUTES = 120

Write-Host "`n⏰ 필터링 시간을 $FILTER_MINUTES 분으로 변경 중...`n" -ForegroundColor Cyan

foreach ($site in $SITES) {
    $functionName = "scandeals-$site"

    Write-Host "[$site] 환경 변수 업데이트 중..." -ForegroundColor Yellow

    aws lambda update-function-configuration `
        --function-name $functionName `
        --environment "Variables={API_URL=http://localhost:8080,API_KEY=test-key-for-development-only,FILTER_MINUTES=$FILTER_MINUTES}" `
        --region $REGION | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 완료!" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 실패!" -ForegroundColor Red
    }

    Start-Sleep -Seconds 2
}

Write-Host "`n✨ 모든 함수 업데이트 완료!`n" -ForegroundColor Cyan
Write-Host "⏳ 배포 완료까지 약 30초 대기 후 테스트하세요.`n" -ForegroundColor Yellow