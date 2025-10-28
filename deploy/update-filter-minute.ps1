$REGION = "ap-northeast-2"
$NEW_FILTER_MINUTES = "360"  # 6시간
$SITES = @("ppomppu", "fmkorea", "quasarzone", "arcalive", "eomisae", "ruliweb")

foreach ($site in $SITES) {
    Write-Host "`n[$site] FILTER_MINUTES 업데이트 중..." -ForegroundColor Yellow

    # Task Definition 가져오기
    $json = aws ecs describe-task-definition --task-definition "scandeals-$site" --region $REGION
    $td = ($json | ConvertFrom-Json).taskDefinition

    # FILTER_MINUTES 변경
    $container = $td.containerDefinitions[0]
    foreach ($env in $container.environment) {
        if ($env.name -eq "FILTER_MINUTES") {
            $env.value = $NEW_FILTER_MINUTES
            Write-Host "  FILTER_MINUTES: $NEW_FILTER_MINUTES" -ForegroundColor Gray
        }
    }

    # 새 Task Definition
    $newTaskDef = @{
        family = $td.family
        executionRoleArn = $td.executionRoleArn
        networkMode = $td.networkMode
        containerDefinitions = @($container)
        requiresCompatibilities = $td.requiresCompatibilities
        cpu = $td.cpu
        memory = $td.memory
    }

    if ($td.taskRoleArn) {
        $newTaskDef.taskRoleArn = $td.taskRoleArn
    }

    # JSON 저장
    $jsonString = $newTaskDef | ConvertTo-Json -Depth 10 -Compress
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText("temp-$site.json", $jsonString, $utf8NoBom)

    # 등록
    $result = aws ecs register-task-definition --cli-input-json file://temp-$site.json --region $REGION 2>&1

    if ($LASTEXITCODE -eq 0) {
        $resultObj = $result | ConvertFrom-Json
        Write-Host "  ✅ 성공: revision $($resultObj.taskDefinition.revision)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 실패" -ForegroundColor Red
    }

    Remove-Item "temp-$site.json" -ErrorAction SilentlyContinue
}

Write-Host "`n확인:" -ForegroundColor Cyan
aws ecs describe-task-definition --task-definition scandeals-ppomppu --region $REGION --query "taskDefinition.containerDefinitions[0].environment"