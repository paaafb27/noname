# test-after-deploy.ps1
# 재배포 후 테스트 스크립트

$REGION = "ap-northeast-2"
$SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")

Write-Host "`n🧪 재배포 후 테스트 시작`n" -ForegroundColor Cyan

$results = @()

foreach ($site in $SITES) {
    Write-Host "[$site] 테스트 중..." -ForegroundColor Yellow
    
    try {
        $result = aws lambda invoke `
            --function-name "scandeals-$site" `
            --region $REGION `
            --log-type Tail `
            --query 'LogResult' `
            --output text `
            response-$site.json 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            # 로그 디코딩
            $logBase64 = $result
            $logBytes = [System.Convert]::FromBase64String($logBase64)
            $logText = [System.Text.Encoding]::UTF8.GetString($logBytes)
            
            # 수집 개수 추출
            $count = 0
            if ($logText -match "수집.*?(\d+)개") {
                $count = $matches[1]
            }
            
            if ($count -gt 0) {
                Write-Host "  ✅ 성공! 수집: $count 개" -ForegroundColor Green
                $results += @{site=$site; status="성공"; count=$count}
            } else {
                Write-Host "  ⚠️  수집 0개" -ForegroundColor Yellow
                $results += @{site=$site; status="경고"; count=0}
            }
        } else {
            Write-Host "  ❌ 실패!" -ForegroundColor Red
            $results += @{site=$site; status="실패"; count="N/A"}
        }
    } catch {
        Write-Host "  ❌ 예외: $_" -ForegroundColor Red
        $results += @{site=$site; status="예외"; count="N/A"}
    }
    
    Write-Host ""
    Start-Sleep -Seconds 2
}

# 결과 요약
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "📊 테스트 결과 요약" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

$successCount = ($results | Where-Object { $_.status -eq "성공" }).Count
Write-Host "✅ 성공: $successCount / 6" -ForegroundColor Green

foreach ($r in $results) {
    $color = switch ($r.status) {
        "성공" { "Green" }
        "경고" { "Yellow" }
        default { "Red" }
    }
    Write-Host "  [$($r.site)] $($r.status) - 수집: $($r.count) 개" -ForegroundColor $color
}

Write-Host ""