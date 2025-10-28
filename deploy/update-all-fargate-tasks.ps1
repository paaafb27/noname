
# 1. AWS 리전
$REGION = "ap-northeast-2"

# 2. 업데이트할 모든 사이트 목록
$SITES = @("ppomppu", "fmkorea", "arcalive", "quasarzone", "ruliweb", "eomisae")

# 3. 적용할 새로운 운영 서버 URL (정확한 전체 경로)
$NEW_API_URL = "https://scandeals.net/api/crawl/data"

# 4. 적용할 실제 API 키
$NEW_API_KEY = "test-key-for-development-only"

# 5. 필터링 시간 (분 단위)
$FILTER_MINUTES_VALUE = "30"

# ==============================================================================

Write-Host "`n🚀 모든 Fargate 크롤러의 Task Definition 업데이트를 시작합니다." -ForegroundColor Cyan
Write-Host " - 적용될 API URL: $NEW_API_URL"
Write-Host " - 적용될 API KEY: $($NEW_API_KEY.Substring(0, 4))... (마스킹됨)"
Write-Host ""

foreach ($site in $SITES) {
    $taskDefFamily = "scandeals-$site"
    Write-Host "[처리 중] '$taskDefFamily' 작업 정의 업데이트..." -ForegroundColor Yellow

    try {
        # 1. 현재 Task Definition 가져오기
        $currentTaskDefJson = aws ecs describe-task-definition `
            --task-definition $taskDefFamily `
            --region $REGION

        $currentTaskDef = $currentTaskDefJson | ConvertFrom-Json

        # 2. 환경 변수 새로 설정
        $newEnvironment = @(
            @{ name = "API_URL"; value = $NEW_API_URL },
            @{ name = "API_KEY"; value = $NEW_API_KEY },
            @{ name = "FILTER_MINUTES"; value = $FILTER_MINUTES_VALUE }
        )

        # 3. 컨테이너 정의 업데이트
        $container = $currentTaskDef.taskDefinition.containerDefinitions[0]
        $container.environment = $newEnvironment

        Write-Host "  - 환경 변수 3개 업데이트 완료" -ForegroundColor Gray

        # 4. 새 Task Definition 등록용 JSON 생성
        $newTaskDef = @{
            family = $currentTaskDef.taskDefinition.family
            taskRoleArn = $currentTaskDef.taskDefinition.taskRoleArn
            executionRoleArn = $currentTaskDef.taskDefinition.executionRoleArn
            networkMode = $currentTaskDef.taskDefinition.networkMode
            containerDefinitions = @($container)
            requiresCompatibilities = $currentTaskDef.taskDefinition.requiresCompatibilities
            cpu = $currentTaskDef.taskDefinition.cpu
            memory = $currentTaskDef.taskDefinition.memory
        }

        # null 값 제거
        if ($null -eq $newTaskDef.taskRoleArn) { $newTaskDef.Remove("taskRoleArn") }

        # 5. JSON 파일로 저장 (UTF8 BOM 없이)
        $tempJsonPath = "temp-$site.json"
        $jsonContent = $newTaskDef | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText($tempJsonPath, $jsonContent, [System.Text.UTF8Encoding]::new($false))

        # 6. 새 Task Definition 등록
        $result = aws ecs register-task-definition `
            --cli-input-json file://$tempJsonPath `
            --region $REGION | ConvertFrom-Json

        Write-Host "  ✅ 성공: 새 리비전 $($result.taskDefinition.revision) 생성" -ForegroundColor Green

        # 임시 파일 삭제
        Remove-Item $tempJsonPath -ErrorAction SilentlyContinue

    } catch {
        Write-Host "  ❌ 실패: '$taskDefFamily' 처리 중 오류 발생" -ForegroundColor Red
        Write-Host "     $($_.Exception.Message)" -ForegroundColor Gray
    }

    Write-Host ""
}

Write-Host "✨ 모든 작업이 완료되었습니다." -ForegroundColor Cyan
Write-Host ""
Write-Host "환경변수 확인:" -ForegroundColor Yellow
aws ecs describe-task-definition `
    --task-definition scandeals-ppomppu `
    --region $REGION `
    --query "taskDefinition.containerDefinitions[0].environment"