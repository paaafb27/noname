# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$REGION = "ap-northeast-2"
$SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")

while ($true) {
    Clear-Host
    Write-Host "`n📊 scanDeals 실시간 모니터링 ($(Get-Date -Format 'HH:mm:ss'))`n" -ForegroundColor Cyan
    Write-Host "="*60 -ForegroundColor Gray

    foreach ($site in $SITES) {
        $logGroup = "/aws/lambda/scandeals-$site"

        try {
            # 최근 10분 로그
            $startTime = [long]([DateTime]::UtcNow.AddMinutes(-10) - [DateTime]"1970-01-01").TotalMilliseconds

            $logStreamsJson = aws logs describe-log-streams `
                --log-group-name $logGroup `
                --order-by LastEventTime `
                --descending `
                --max-items 1 `
                --region $REGION 2>$null

            if (-not $logStreamsJson) {
                Write-Host "[$site] ⏸️  실행 기록 없음" -ForegroundColor Gray
                continue
            }

            $logStreams = $logStreamsJson | ConvertFrom-Json

            if ($logStreams.logStreams.Count -eq 0) {
                Write-Host "[$site] ⏸️  실행 기록 없음" -ForegroundColor Gray
                continue
            }

            $latestStream = $logStreams.logStreams[0].logStreamName
            $lastEventTime = [DateTimeOffset]::FromUnixTimeMilliseconds($logStreams.logStreams[0].lastEventTimestamp)

            # 최신 로그 이벤트 가져오기
            $eventsJson = aws logs get-log-events `
                --log-group-name $logGroup `
                --log-stream-name $latestStream `
                --start-time $startTime `
                --limit 50 `
                --region $REGION 2>$null

            if (-not $eventsJson) {
                Write-Host "[$site] ⚠️  로그 없음" -ForegroundColor Yellow
                continue
            }

            # JSON 파싱 에러 처리
            $events = $null
            try {
                $events = $eventsJson | ConvertFrom-Json
            } catch {
                Write-Host "[$site] ⚠️  로그 파싱 실패" -ForegroundColor Yellow
                continue
            }

            $collectCount = 0
            $hasError = $false

            foreach ($event in $events.events) {
                $msg = $event.message
                if ($msg -match "총\s+(\d+)개\s+수집|✅.*?(\d+)개\s+수집") {
                    $collectCount = if ($matches[1]) { [int]$matches[1] } else { [int]$matches[2] }
                }
                if ($msg -match "ERROR|Exception|Traceback|실패") {
                    $hasError = $true
                }
            }

            $statusIcon = if ($hasError) { "❌" } elseif ($collectCount -gt 0) { "✅" } else { "⚠️ " }
            $timeAgo = (Get-Date) - $lastEventTime.LocalDateTime
            $timeAgoStr = if ($timeAgo.TotalMinutes -lt 60) {
                "$([int]$timeAgo.TotalMinutes)분 전"
            } else {
                "$([int]$timeAgo.TotalHours)시간 전"
            }

            Write-Host "[$site] $statusIcon 수집: $collectCount 개 | 마지막 실행: $timeAgoStr" -ForegroundColor $(if ($hasError) { "Red" } elseif ($collectCount -gt 0) { "Green" } else { "Yellow" })

        } catch {
            Write-Host "[$site] ❌ 모니터링 실패: $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    Write-Host "`n다음 업데이트까지 30초..." -ForegroundColor Gray
    Start-Sleep -Seconds 30
}