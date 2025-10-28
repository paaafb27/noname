# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$REGION = "ap-northeast-2"
$SITE = "fmkorea"  # 또는 다른 사이트

Write-Host "`n📡 $SITE 실시간 로그 모니터링 (Ctrl+C로 종료)`n" -ForegroundColor Cyan

aws logs tail "/aws/lambda/scandeals-$SITE" `
    --follow `
    --format short `
    --region $REGION