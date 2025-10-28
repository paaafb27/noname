# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$REGION = "ap-northeast-2"

Write-Host "`n📊 모니터링 대시보드 생성 중...`n" -ForegroundColor Cyan

# AWS CloudWatch Dashboard - 간단한 4개 위젯만
$dashboardJson = '{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Invocations", { "stat": "Sum" } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-2",
        "title": "Lambda Invocations",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Errors", { "stat": "Sum", "color": "#d62728" } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-2",
        "title": "Lambda Errors",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Duration", { "stat": "Average" } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-2",
        "title": "Lambda Duration (ms)",
        "period": 300
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Throttles", { "stat": "Sum" } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-2",
        "title": "Lambda Throttles",
        "period": 300
      }
    }
  ]
}'

# JSON을 임시 파일로 저장 (BOM 없는 UTF-8)
$tempFile = ".\dashboard-temp.json"
[System.IO.File]::WriteAllText($tempFile, $dashboardJson, [System.Text.UTF8Encoding]::new($false))

# 대시보드 생성
Write-Host "대시보드 생성 요청 중..." -ForegroundColor Yellow
$result = aws cloudwatch put-dashboard `
    --dashboard-name "scandeals-monitoring" `
    --dashboard-body file://$tempFile `
    --region $REGION 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ 대시보드 생성 완료!" -ForegroundColor Green
    Write-Host "`n📊 생성된 위젯:" -ForegroundColor Cyan
    Write-Host "  1. Lambda Invocations - 총 실행 횟수" -ForegroundColor White
    Write-Host "  2. Lambda Errors - 에러 발생 수" -ForegroundColor White
    Write-Host "  3. Lambda Duration - 평균 실행 시간" -ForegroundColor White
    Write-Host "  4. Lambda Throttles - 제한 발생 수`n" -ForegroundColor White

    Write-Host "🔗 대시보드 링크:" -ForegroundColor Cyan
    Write-Host "https://console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=scandeals-monitoring`n" -ForegroundColor White
} else {
    Write-Host "`n❌ 대시보드 생성 실패!" -ForegroundColor Red
    Write-Host "에러 메시지:" -ForegroundColor Yellow
    Write-Host $result -ForegroundColor Red

    Write-Host "`n생성된 JSON:" -ForegroundColor Yellow
    Get-Content $tempFile
}

# 임시 파일 삭제
Start-Sleep -Seconds 2
Remove-Item $tempFile -ErrorAction SilentlyContinue

Write-Host "완료!`n" -ForegroundColor Gray