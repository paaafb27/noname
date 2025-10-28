# eventbridge-schedule-setup.ps1
$REGION = "ap-northeast-2"
$SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")

Write-Host "`n⏰ EventBridge 스케줄 설정 시작`n" -ForegroundColor Cyan

foreach ($site in $SITES) {
    $ruleName = "scandeals-$site-schedule"
    $functionName = "scandeals-$site"
    $functionArn = "arn:aws:lambda:$REGION:YOUR_ACCOUNT_ID:function:$functionName"

    Write-Host "[$site] 스케줄 생성 중..." -ForegroundColor Yellow

    # 1. EventBridge 규칙 생성 (10분마다 실행)
    aws events put-rule `
        --name $ruleName `
        --schedule-expression "rate(10 minutes)" `
        --state ENABLED `
        --region $REGION | Out-Null

    # 2. Lambda 함수에 권한 부여
    aws lambda add-permission `
        --function-name $functionName `
        --statement-id "EventBridgeInvoke-$site" `
        --action "lambda:InvokeFunction" `
        --principal events.amazonaws.com `
        --source-arn "arn:aws:events:$REGION:YOUR_ACCOUNT_ID:rule/$ruleName" `
        --region $REGION 2>$null

    # 3. 규칙에 타겟 설정
    aws events put-targets `
        --rule $ruleName `
        --targets "Id=1,Arn=$functionArn" `
        --region $REGION | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 스케줄 설정 완료!" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 실패!" -ForegroundColor Red
    }
}

Write-Host "`n✨ 모든 스케줄 설정 완료!`n" -ForegroundColor Cyan
Write-Host "📊 확인: https://console.aws.amazon.com/events/home?region=$REGION#/rules`n" -ForegroundColor Gray