# EventBridge Target 수동 설정 스크립트
# Rule은 이미 생성되어 있으므로 Target만 추가

$ACCOUNT_ID = "127679825681"
$REGION = "ap-northeast-2"
$CLUSTER = "scandeals-crawler-cluster"
$SUBNET_ID = "subnet-0cf0b2476d85e7adb"
$SG_ID = "sg-06b877fb23276fcbf"
$SITES = @("ruliweb", "quasarzone", "arcalive", "eomisae", "fmkorea")


Write-Host "================================" -ForegroundColor Magenta
Write-Host "EventBridge Target 설정" -ForegroundColor Magenta
Write-Host "================================`n" -ForegroundColor Magenta

foreach ($site in $SITES) {
    $ruleName = "scandeals-${site}-schedule"

    Write-Host "[$site] Target 설정..." -ForegroundColor Yellow

    # Target JSON 직접 생성 (Here-String 대신 JSON 직렬화)
    $targetConfig = @{
        Id = "1"
        Arn = "arn:aws:ecs:${REGION}:${ACCOUNT_ID}:cluster/${CLUSTER}"
        RoleArn = "arn:aws:iam::${ACCOUNT_ID}:role/ecsEventsRole"
        EcsParameters = @{
            TaskDefinitionArn = "arn:aws:ecs:${REGION}:${ACCOUNT_ID}:task-definition/scandeals-${site}"
            TaskCount = 1
            LaunchType = "FARGATE"
            NetworkConfiguration = @{
                awsvpcConfiguration = @{
                    Subnets = @($SUBNET_ID)
                    SecurityGroups = @($SG_ID)
                    AssignPublicIp = "ENABLED"
                }
            }
        }
    }

    # JSON 변환 및 파일 저장 (ASCII, BOM 없이)
    $targetJson = "[$($targetConfig | ConvertTo-Json -Depth 10 -Compress)]"
    [System.IO.File]::WriteAllText("$PWD\target-$site.json", $targetJson, [System.Text.Encoding]::ASCII)

    # Target 설정
    $result = aws events put-targets `
        --rule $ruleName `
        --targets "file://target-$site.json" `
        --region $REGION 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Target 설정 완료" -ForegroundColor Green
        Remove-Item "target-$site.json" -ErrorAction SilentlyContinue
    } else {
        Write-Host "  ❌ Target 설정 실패" -ForegroundColor Red
        Write-Host "     오류: $result" -ForegroundColor Red
        Write-Host "     JSON 파일: target-$site.json (수동 확인용 보존)" -ForegroundColor Yellow
    }
}

Write-Host "`n================================" -ForegroundColor Magenta
Write-Host "✅ Target 설정 완료!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Magenta

Write-Host "`n다음 실행 시간: 현재부터 10분 후" -ForegroundColor Cyan
Write-Host "즉시 테스트하려면:" -ForegroundColor White
Write-Host "  .\run-task-manual-test.ps1`n" -ForegroundColor Cyan