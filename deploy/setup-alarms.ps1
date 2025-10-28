# F:\scandeals-crawler\deploy\setup-alarms.ps1
$REGION = "ap-northeast-2"
$ACCOUNT_ID = "127679825681"
$EMAIL = "paaafb27@gmail.com"  # ⚠️ 실제 이메일로 변경!
$SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")

Write-Host "`n🔔 CloudWatch 알람 설정 시작`n" -ForegroundColor Cyan

# SNS 토픽 생성
Write-Host "SNS 토픽 생성 중..." -ForegroundColor Yellow
$snsResult = aws sns create-topic --name scandeals-alerts --region $REGION 2>$null | ConvertFrom-Json

if ($snsResult) {
    $SNS_TOPIC = $snsResult.TopicArn
    Write-Host "  ✅ SNS 토픽 생성 완료: $SNS_TOPIC" -ForegroundColor Green
} else {
    # 이미 존재하는 경우
    $SNS_TOPIC = "arn:aws:sns:$REGION`:$ACCOUNT_ID`:scandeals-alerts"
    Write-Host "  ℹ️  기존 SNS 토픽 사용: $SNS_TOPIC" -ForegroundColor Cyan
}

# 이메일 구독
Write-Host "`n이메일 구독 설정: $EMAIL" -ForegroundColor Yellow
aws sns subscribe `
    --topic-arn $SNS_TOPIC `
    --protocol email `
    --notification-endpoint $EMAIL `
    --region $REGION 2>$null

Write-Host "  ⚠️  이메일 인증 필요! 받은 메일에서 'Confirm subscription' 클릭하세요.`n" -ForegroundColor Yellow

# 각 함수별 알람 설정
foreach ($site in $SITES) {
    $functionName = "scandeals-$site"
    $alarmName = "scandeals-$site-errors"

    Write-Host "[$site] 에러 알람 생성 중..." -ForegroundColor Yellow

    aws cloudwatch put-metric-alarm `
        --alarm-name $alarmName `
        --alarm-description "scandeals-$site Lambda 에러 발생 시 알림" `
        --metric-name Errors `
        --namespace AWS/Lambda `
        --statistic Sum `
        --period 300 `
        --threshold 1 `
        --comparison-operator GreaterThanOrEqualToThreshold `
        --evaluation-periods 1 `
        --dimensions Name=FunctionName,Value=$functionName `
        --alarm-actions $SNS_TOPIC `
        --region $REGION | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 알람 설정 완료!" -ForegroundColor Green
    }

    # 타임아웃 알람
    $timeoutAlarmName = "scandeals-$site-timeout"
    Write-Host "[$site] 타임아웃 알람 생성 중..." -ForegroundColor Yellow

    aws cloudwatch put-metric-alarm `
        --alarm-name $timeoutAlarmName `
        --alarm-description "scandeals-$site Lambda 타임아웃 알림" `
        --metric-name Duration `
        --namespace AWS/Lambda `
        --statistic Maximum `
        --period 300 `
        --threshold 850000 `
        --comparison-operator GreaterThanThreshold `
        --evaluation-periods 1 `
        --dimensions Name=FunctionName,Value=$functionName `
        --alarm-actions $SNS_TOPIC `
        --region $REGION | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 타임아웃 알람 설정 완료!" -ForegroundColor Green
    }
}

Write-Host "`n✨ 모든 알람 설정 완료!`n" -ForegroundColor Cyan
Write-Host "📧 $EMAIL 로 알림이 전송됩니다.`n" -ForegroundColor Gray
Write-Host "🔗 확인: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#alarmsV2:`n" -ForegroundColor Gray