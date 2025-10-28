# check-logs.ps1
# Lambda 로그 상세 확인

$REGION = "ap-northeast-2"
$SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

foreach ($site in $SITES) {
    Write-Host "`n========== [$site] ==========" -ForegroundColor Cyan
    
    $logs = aws logs tail "/aws/lambda/scandeals-$site" `
        --since 10m `
        --format short `
        --region $REGION 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $logLines = $logs -split "`n" | Select-Object -Last 15
        foreach ($line in $logLines) {
            if ($line -match "수집|에러|ERROR|실패|FAIL|0개|완료") {
                Write-Host $line -ForegroundColor White
            }
        }
    } else {
        Write-Host "로그 없음" -ForegroundColor Red
    }
}