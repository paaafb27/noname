# 개선된 ECS Task 수동 실행 테스트 스크립트
# 에러 처리 개선 버전

$REGION = "ap-northeast-2"
$CLUSTER_NAME = "scandeals-crawler-cluster"

# ========================================
# ⚠️ 필수: 실제 값으로 변경 필요
# ========================================
$SUBNET_ID = "subnet-0cf0b2476d85e7adb"
$SG_ID = "sg-06b877fb23276fcbf"
# ========================================

Write-Host "================================" -ForegroundColor Magenta
Write-Host "ECS Task 수동 실행 테스트" -ForegroundColor Magenta
Write-Host "================================`n" -ForegroundColor Magenta

# Subnet과 SG 설정 확인
if ($SUBNET_ID -eq "subnet-xxxxxxxxx" -or $SG_ID -eq "sg-xxxxxxxxx") {
    Write-Host "❌ 오류: SUBNET_ID와 SG_ID를 실제 값으로 변경해주세요`n" -ForegroundColor Red
    exit 1
}

# 테스트할 사이트 선택
$testSite = "quasarzone"
Write-Host "테스트 사이트: $testSite`n" -ForegroundColor Cyan

# 사전 확인 1: Cluster 존재
Write-Host "[사전 확인 1] Cluster 확인" -ForegroundColor Yellow
$clusterCheck = aws ecs describe-clusters --clusters $CLUSTER_NAME --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Cluster 없음 또는 접근 불가" -ForegroundColor Red
    Write-Host "     오류: $clusterCheck" -ForegroundColor Red
    Write-Host "`n  생성 명령:" -ForegroundColor Yellow
    Write-Host "  aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $REGION" -ForegroundColor Cyan
    exit 1
}
Write-Host "  ✅ Cluster 존재`n" -ForegroundColor Green

# 사전 확인 2: Task Definition 존재
Write-Host "[사전 확인 2] Task Definition 확인" -ForegroundColor Yellow
$taskDefCheck = aws ecs describe-task-definition --task-definition "scandeals-$testSite" --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Task Definition 없음" -ForegroundColor Red
    Write-Host "     오류: $taskDefCheck" -ForegroundColor Red
    Write-Host "`n  생성 명령:" -ForegroundColor Yellow
    Write-Host "  .\create-task-definitions.ps1" -ForegroundColor Cyan
    exit 1
}
$taskDefObj = $taskDefCheck | ConvertFrom-Json
$revision = $taskDefObj.taskDefinition.revision
Write-Host "  ✅ Task Definition 존재: revision $revision`n" -ForegroundColor Green

# 사전 확인 3: Subnet 존재
Write-Host "[사전 확인 3] Subnet 확인" -ForegroundColor Yellow
$subnetCheck = aws ec2 describe-subnets --subnet-ids $SUBNET_ID --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Subnet 없음 또는 잘못된 ID" -ForegroundColor Red
    Write-Host "     입력된 ID: $SUBNET_ID" -ForegroundColor Red
    Write-Host "     오류: $subnetCheck" -ForegroundColor Red
    Write-Host "`n  조회 명령:" -ForegroundColor Yellow
    Write-Host "  .\get-network-info.ps1" -ForegroundColor Cyan
    exit 1
}
Write-Host "  ✅ Subnet 존재`n" -ForegroundColor Green

# 사전 확인 4: Security Group 존재
Write-Host "[사전 확인 4] Security Group 확인" -ForegroundColor Yellow
$sgCheck = aws ec2 describe-security-groups --group-ids $SG_ID --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Security Group 없음 또는 잘못된 ID" -ForegroundColor Red
    Write-Host "     입력된 ID: $SG_ID" -ForegroundColor Red
    Write-Host "     오류: $sgCheck" -ForegroundColor Red
    Write-Host "`n  조회 명령:" -ForegroundColor Yellow
    Write-Host "  .\get-network-info.ps1" -ForegroundColor Cyan
    exit 1
}
Write-Host "  ✅ Security Group 존재`n" -ForegroundColor Green

# Task 실행
Write-Host "[1] Task 실행 중..." -ForegroundColor Yellow
Write-Host "    Cluster: $CLUSTER_NAME" -ForegroundColor Gray
Write-Host "    Task Definition: scandeals-$testSite" -ForegroundColor Gray
Write-Host "    Subnet: $SUBNET_ID" -ForegroundColor Gray
Write-Host "    Security Group: $SG_ID`n" -ForegroundColor Gray

$runTaskOutput = aws ecs run-task `
    --cluster $CLUSTER_NAME `
    --task-definition "scandeals-$testSite" `
    --launch-type FARGATE `
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" `
    --region $REGION 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Task 실행 실패" -ForegroundColor Red
    Write-Host "`n=== 전체 오류 메시지 ===" -ForegroundColor Yellow
    Write-Host $runTaskOutput -ForegroundColor Red
    Write-Host "========================`n" -ForegroundColor Yellow

    # 일반적인 오류 원인 분석
    if ($runTaskOutput -like "*CannotPullContainerError*") {
        Write-Host "원인: ECR 이미지를 가져올 수 없음" -ForegroundColor Yellow
        Write-Host "해결:" -ForegroundColor White
        Write-Host "  1. ECR 이미지 존재 확인:" -ForegroundColor Gray
        Write-Host "     aws ecr describe-images --repository-name scandeals-crawler --region $REGION" -ForegroundColor Cyan
        Write-Host "  2. IAM Role에 ECR 권한 확인:" -ForegroundColor Gray
        Write-Host "     aws iam get-role-policy --role-name ecsTaskExecutionRole --policy-name ECSTaskExecutionRolePolicy" -ForegroundColor Cyan
    }
    elseif ($runTaskOutput -like "*ResourceInitializationError*") {
        Write-Host "원인: 네트워크 초기화 실패" -ForegroundColor Yellow
        Write-Host "해결:" -ForegroundColor White
        Write-Host "  1. Public IP 할당 가능한 Subnet인지 확인" -ForegroundColor Gray
        Write-Host "  2. Security Group의 Outbound 규칙 확인 (HTTPS 443)" -ForegroundColor Gray
    }
    elseif ($runTaskOutput -like "*does not have permission*" -or $runTaskOutput -like "*is not authorized*") {
        Write-Host "원인: IAM 권한 부족" -ForegroundColor Yellow
        Write-Host "해결:" -ForegroundColor White
        Write-Host "  ecsTaskExecutionRole에 필요한 권한 확인" -ForegroundColor Gray
    }

    exit 1
}

# JSON 파싱
try {
    $runTaskResult = $runTaskOutput | ConvertFrom-Json
}
catch {
    Write-Host "  ❌ 응답 파싱 실패" -ForegroundColor Red
    Write-Host "     응답 내용:" -ForegroundColor Yellow
    Write-Host $runTaskOutput -ForegroundColor Gray
    exit 1
}

# Task 실행 확인
if ($runTaskResult.tasks.Count -eq 0) {
    Write-Host "  ❌ Task가 시작되지 않음" -ForegroundColor Red

    if ($runTaskResult.failures.Count -gt 0) {
        Write-Host "`n  실패 원인:" -ForegroundColor Yellow
        foreach ($failure in $runTaskResult.failures) {
            Write-Host "    - $($failure.reason)" -ForegroundColor Red
            if ($failure.detail) {
                Write-Host "      상세: $($failure.detail)" -ForegroundColor Gray
            }
        }
    }
    exit 1
}

$taskArn = $runTaskResult.tasks[0].taskArn
$taskId = $taskArn.Split('/')[-1]

Write-Host "  ✅ Task 시작됨" -ForegroundColor Green
Write-Host "     Task ID: $taskId" -ForegroundColor Gray
Write-Host "     ARN: $taskArn`n" -ForegroundColor Gray

# Task 상태 모니터링
Write-Host "[2] Task 상태 모니터링 (30초 대기)..." -ForegroundColor Yellow

for ($i = 1; $i -le 6; $i++) {
    Start-Sleep -Seconds 5

    $taskStatus = aws ecs describe-tasks `
        --cluster $CLUSTER_NAME `
        --tasks $taskArn `
        --region $REGION | ConvertFrom-Json

    $task = $taskStatus.tasks[0]
    $status = $task.lastStatus

    Write-Host "  [$i/6] 상태: $status" -ForegroundColor Cyan

    if ($status -eq "STOPPED") {
        Write-Host "`n  ⚠️  Task가 중지되었습니다" -ForegroundColor Yellow
        Write-Host "     중지 이유: $($task.stoppedReason)" -ForegroundColor Red

        if ($task.containers[0].exitCode) {
            Write-Host "     Exit Code: $($task.containers[0].exitCode)" -ForegroundColor Red

            # Exit Code에 따른 원인 분석
            switch ($task.containers[0].exitCode) {
                1 { Write-Host "     → 일반적인 애플리케이션 오류" -ForegroundColor Yellow }
                137 { Write-Host "     → 메모리 부족 (OOM Killed)" -ForegroundColor Yellow }
                139 { Write-Host "     → Segmentation Fault" -ForegroundColor Yellow }
                143 { Write-Host "     → SIGTERM (정상 종료 시그널)" -ForegroundColor Yellow }
            }
        }

        if ($task.containers[0].reason) {
            Write-Host "     컨테이너 중지 이유: $($task.containers[0].reason)" -ForegroundColor Red
        }

        break
    }

    if ($status -eq "RUNNING") {
        Write-Host "  ✅ Task 정상 실행 중`n" -ForegroundColor Green
        break
    }
}

# 로그 확인
Write-Host "[3] CloudWatch 로그 확인 (10초 후)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`n--- 로그 출력 시작 ---" -ForegroundColor Magenta
$logs = aws logs tail "/ecs/scandeals-$testSite" --since 2m --region $REGION 2>&1

if ($LASTEXITCODE -eq 0 -and $logs) {
    Write-Host $logs -ForegroundColor White
} else {
    Write-Host "⚠️  로그가 없거나 Log Group이 생성되지 않았습니다" -ForegroundColor Yellow
    Write-Host "Log Group: /ecs/scandeals-$testSite" -ForegroundColor Gray

    # Log Group 생성 여부 확인
    $logGroupCheck = aws logs describe-log-groups --log-group-name-prefix "/ecs/scandeals-$testSite" --region $REGION 2>&1 | ConvertFrom-Json

    if ($logGroupCheck.logGroups.Count -eq 0) {
        Write-Host "`n  Log Group이 없습니다. 생성 명령:" -ForegroundColor Yellow
        Write-Host "  aws logs create-log-group --log-group-name /ecs/scandeals-$testSite --region $REGION" -ForegroundColor Cyan
    }
}
Write-Host "--- 로그 출력 끝 ---`n" -ForegroundColor Magenta

# 실시간 로그 모니터링 제안
Write-Host "[4] 실시간 로그 모니터링" -ForegroundColor Yellow
Write-Host "  다음 명령으로 실시간 로그 확인:" -ForegroundColor White
Write-Host "  aws logs tail /ecs/scandeals-$testSite --follow --region $REGION`n" -ForegroundColor Cyan

Write-Host "================================`n" -ForegroundColor Magenta