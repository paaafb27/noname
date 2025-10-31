# ECS Task 실행 상태 종합 진단 스크립트

$ACCOUNT_ID = "127679825681"
$REGION = "ap-northeast-2"
$CLUSTER_NAME = "scandeals-cluster"
$SITES = @("ruliweb", "quasarzone", "arcalive", "eomisae", "fmkorea")

Write-Host "================================" -ForegroundColor Magenta
Write-Host "ECS Task 실행 상태 종합 진단" -ForegroundColor Magenta
Write-Host "================================`n" -ForegroundColor Magenta

# 1. Cluster 존재 확인
Write-Host "[1] Cluster 확인" -ForegroundColor Yellow
$clusterCheck = aws ecs describe-clusters --clusters $CLUSTER_NAME --region $REGION 2>&1 | ConvertFrom-Json
if ($clusterCheck.clusters.Count -gt 0) {
    Write-Host "  ✅ Cluster 존재: $CLUSTER_NAME" -ForegroundColor Green
    Write-Host "     - 상태: $($clusterCheck.clusters[0].status)" -ForegroundColor Gray
    Write-Host "     - Running Tasks: $($clusterCheck.clusters[0].runningTasksCount)" -ForegroundColor Gray
} else {
    Write-Host "  ❌ Cluster 없음: $CLUSTER_NAME" -ForegroundColor Red
    Write-Host "     다음 명령으로 생성:" -ForegroundColor Yellow
    Write-Host "     aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $REGION" -ForegroundColor Cyan
    exit 1
}

# 2. Task Definition 확인
Write-Host "`n[2] Task Definition 확인" -ForegroundColor Yellow
foreach ($site in $SITES) {
    $taskFamily = "scandeals-$site"
    $taskDef = aws ecs describe-task-definition --task-definition $taskFamily --region $REGION 2>&1

    if ($LASTEXITCODE -eq 0) {
        $taskDefObj = $taskDef | ConvertFrom-Json
        $revision = $taskDefObj.taskDefinition.revision
        Write-Host "  ✅ $taskFamily : revision $revision" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $taskFamily : 없음" -ForegroundColor Red
    }
}

# 3. CloudWatch Log Group 확인
Write-Host "`n[3] CloudWatch Log Group 확인" -ForegroundColor Yellow
foreach ($site in $SITES) {
    $logGroup = "/ecs/scandeals-$site"
    $logCheck = aws logs describe-log-groups --log-group-name-prefix $logGroup --region $REGION 2>&1 | ConvertFrom-Json

    if ($logCheck.logGroups.Count -gt 0) {
        Write-Host "  ✅ $logGroup : 존재" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $logGroup : 없음 (자동 생성됨)" -ForegroundColor Yellow
    }
}

# 4. 최근 Task 실행 기록 확인
Write-Host "`n[4] 최근 Task 실행 기록 (최근 1시간)" -ForegroundColor Yellow
foreach ($site in $SITES) {
    $taskFamily = "scandeals-$site"

    # 최근 실행된 Task 조회
    $tasks = aws ecs list-tasks --cluster $CLUSTER_NAME --family $taskFamily --region $REGION 2>&1 | ConvertFrom-Json

    if ($tasks.taskArns.Count -gt 0) {
        Write-Host "  [$site] 실행 중인 Task 발견" -ForegroundColor Cyan

        # Task 상세 정보
        $taskDetails = aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $tasks.taskArns[0] --region $REGION | ConvertFrom-Json
        $task = $taskDetails.tasks[0]

        Write-Host "     - Task ID: $($task.taskArn.Split('/')[-1])" -ForegroundColor Gray
        Write-Host "     - 상태: $($task.lastStatus)" -ForegroundColor Gray
        Write-Host "     - 시작 시간: $($task.startedAt)" -ForegroundColor Gray

        if ($task.stopCode) {
            Write-Host "     - 중지 이유: $($task.stoppedReason)" -ForegroundColor Red
        }
    } else {
        Write-Host "  [$site] ⚠️  최근 실행 기록 없음" -ForegroundColor Yellow
    }
}

# 5. EventBridge Rule 확인
Write-Host "`n[5] EventBridge Rule 확인" -ForegroundColor Yellow
foreach ($site in $SITES) {
    $ruleName = "scandeals-${site}-schedule"
    $ruleCheck = aws events describe-rule --name $ruleName --region $REGION 2>&1

    if ($LASTEXITCODE -eq 0) {
        $ruleObj = $ruleCheck | ConvertFrom-Json
        Write-Host "  ✅ $ruleName" -ForegroundColor Green
        Write-Host "     - 스케줄: $($ruleObj.ScheduleExpression)" -ForegroundColor Gray
        Write-Host "     - 상태: $($ruleObj.State)" -ForegroundColor Gray

        # Target 확인
        $targets = aws events list-targets-by-rule --rule $ruleName --region $REGION | ConvertFrom-Json
        if ($targets.Targets.Count -gt 0) {
            Write-Host "     - Target: 설정됨 (ECS Task)" -ForegroundColor Gray
        } else {
            Write-Host "     - Target: ❌ 없음" -ForegroundColor Red
        }
    } else {
        Write-Host "  ❌ $ruleName : 없음" -ForegroundColor Red
    }
}

# 6. ECR 이미지 확인
Write-Host "`n[6] ECR 이미지 확인" -ForegroundColor Yellow
foreach ($site in $SITES) {
    $imageTag = "${site}-latest"
    $images = aws ecr describe-images --repository-name scandeals-crawler --region $REGION 2>&1 | ConvertFrom-Json

    $foundImage = $images.imageDetails | Where-Object { $_.imageTags -contains $imageTag }

    if ($foundImage) {
        $pushedDate = [DateTime]::Parse($foundImage.imagePushedAt).ToString("yyyy-MM-dd HH:mm")
        Write-Host "  ✅ $imageTag : $pushedDate" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $imageTag : 없음" -ForegroundColor Red
    }
}

# 7. 네트워크 설정 확인 (VPC, Subnet, Security Group)
Write-Host "`n[7] 네트워크 설정 확인" -ForegroundColor Yellow
Write-Host "  ⚠️  수동 확인 필요:" -ForegroundColor Yellow
Write-Host "     - VPC에 Public Subnet이 있는지 확인" -ForegroundColor Gray
Write-Host "     - Security Group의 Outbound 규칙 확인 (443 포트)" -ForegroundColor Gray
Write-Host "     - Task에 Public IP 할당 설정 확인" -ForegroundColor Gray

# 8. 권장 조치사항
Write-Host "`n================================" -ForegroundColor Magenta
Write-Host "권장 조치사항" -ForegroundColor Magenta
Write-Host "================================" -ForegroundColor Magenta

Write-Host "`n[즉시 실행 가능한 조치]" -ForegroundColor Cyan
Write-Host "1. Task Definition이 없는 경우:" -ForegroundColor White
Write-Host "   → create-task-definitions.ps1 실행" -ForegroundColor Gray

Write-Host "`n2. EventBridge Rule이 없는 경우:" -ForegroundColor White
Write-Host "   → create-eventbridge-rules.ps1 실행" -ForegroundColor Gray

Write-Host "`n3. 수동으로 Task 실행 테스트:" -ForegroundColor White
Write-Host "   # Subnet ID와 Security Group ID를 실제 값으로 변경" -ForegroundColor Yellow
Write-Host @"
   `$SUBNET_ID = "subnet-xxxxxxxxx"
   `$SG_ID = "sg-xxxxxxxxx"

   aws ecs run-task \
       --cluster $CLUSTER_NAME \
       --task-definition scandeals-ruliweb \
       --launch-type FARGATE \
       --network-configuration "awsvpcConfiguration={subnets=[`$SUBNET_ID],securityGroups=[`$SG_ID],assignPublicIp=ENABLED}" \
       --region $REGION
"@ -ForegroundColor Cyan

Write-Host "`n4. 실행 후 로그 확인 (1-2분 대기 후):" -ForegroundColor White
Write-Host "   aws logs tail /ecs/scandeals-ruliweb --since 5m --follow --region $REGION" -ForegroundColor Cyan

Write-Host "`n================================`n" -ForegroundColor Magenta