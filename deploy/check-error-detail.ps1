# ECS Task 실행 에러 원인 확인 스크립트

$REGION = "ap-northeast-2"
$CLUSTER_NAME = "scandeals-cluster"
$SUBNET_ID = "subnet-0c41ae8ab41f6f1e7"
$SG_ID = "sg-0a06f21f6e0ba61d0"
$testSite = "ppomppu"

Write-Host "================================" -ForegroundColor Magenta
Write-Host "에러 원인 상세 확인" -ForegroundColor Magenta
Write-Host "================================`n" -ForegroundColor Magenta

# 실제 AWS CLI 명령 실행 후 원시 출력 확인
Write-Host "[1] Task 실행 시도 (원시 출력 확인)" -ForegroundColor Yellow
Write-Host "명령어:" -ForegroundColor Gray
$command = "aws ecs run-task --cluster $CLUSTER_NAME --task-definition scandeals-$testSite --launch-type FARGATE --network-configuration `"awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}`" --region $REGION"
Write-Host $command -ForegroundColor Cyan
Write-Host "`n실행 결과:" -ForegroundColor Gray
Write-Host "---" -ForegroundColor DarkGray

$output = aws ecs run-task `
    --cluster $CLUSTER_NAME `
    --task-definition "scandeals-$testSite" `
    --launch-type FARGATE `
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" `
    --region $REGION 2>&1

Write-Host $output
Write-Host "---`n" -ForegroundColor DarkGray

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Exit Code: $LASTEXITCODE`n" -ForegroundColor Red

    # 오류 유형 분석
    Write-Host "[2] 오류 유형 분석" -ForegroundColor Yellow

    if ($output -like "*InvalidParameterException*") {
        Write-Host "  → 잘못된 파라미터" -ForegroundColor Red
        Write-Host "     Subnet ID, Security Group ID, Cluster 이름 확인 필요`n" -ForegroundColor Yellow
    }
    elseif ($output -like "*ClusterNotFoundException*") {
        Write-Host "  → Cluster가 존재하지 않음" -ForegroundColor Red
        Write-Host "     생성 명령: aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $REGION`n" -ForegroundColor Cyan
    }
    elseif ($output -like "*unable to find*" -or $output -like "*does not exist*") {
        Write-Host "  → Task Definition이 존재하지 않음" -ForegroundColor Red
        Write-Host "     생성 명령: .\create-task-definitions.ps1`n" -ForegroundColor Cyan
    }
    elseif ($output -like "*AccessDenied*" -or $output -like "*not authorized*") {
        Write-Host "  → IAM 권한 부족" -ForegroundColor Red
        Write-Host "     AWS 자격증명 및 권한 확인 필요`n" -ForegroundColor Yellow
    }

    # 각 리소스 개별 확인
    Write-Host "[3] 리소스 개별 확인" -ForegroundColor Yellow

    # Cluster 확인
    Write-Host "`n  [3-1] Cluster 확인" -ForegroundColor Cyan
    $clusterResult = aws ecs describe-clusters --clusters $CLUSTER_NAME --region $REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ Cluster 존재" -ForegroundColor Green
    } else {
        Write-Host "    ❌ Cluster 확인 실패" -ForegroundColor Red
        Write-Host "       $clusterResult" -ForegroundColor Gray
    }

    # Task Definition 확인
    Write-Host "`n  [3-2] Task Definition 확인" -ForegroundColor Cyan
    $taskDefResult = aws ecs describe-task-definition --task-definition "scandeals-$testSite" --region $REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ Task Definition 존재" -ForegroundColor Green
    } else {
        Write-Host "    ❌ Task Definition 확인 실패" -ForegroundColor Red
        Write-Host "       $taskDefResult" -ForegroundColor Gray
    }

    # Subnet 확인
    Write-Host "`n  [3-3] Subnet 확인" -ForegroundColor Cyan
    $subnetResult = aws ec2 describe-subnets --subnet-ids $SUBNET_ID --region $REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ Subnet 존재" -ForegroundColor Green
    } else {
        Write-Host "    ❌ Subnet 확인 실패" -ForegroundColor Red
        Write-Host "       입력된 ID: $SUBNET_ID" -ForegroundColor Yellow
        Write-Host "       $subnetResult" -ForegroundColor Gray
    }

    # Security Group 확인
    Write-Host "`n  [3-4] Security Group 확인" -ForegroundColor Cyan
    $sgResult = aws ec2 describe-security-groups --group-ids $SG_ID --region $REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ Security Group 존재" -ForegroundColor Green
    } else {
        Write-Host "    ❌ Security Group 확인 실패" -ForegroundColor Red
        Write-Host "       입력된 ID: $SG_ID" -ForegroundColor Yellow
        Write-Host "       $sgResult" -ForegroundColor Gray
    }

    # IAM Role 확인
    Write-Host "`n  [3-5] IAM Role 확인" -ForegroundColor Cyan
    $roleResult = aws iam get-role --role-name ecsTaskExecutionRole 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✅ ecsTaskExecutionRole 존재" -ForegroundColor Green
    } else {
        Write-Host "    ❌ ecsTaskExecutionRole 확인 실패" -ForegroundColor Red
        Write-Host "       $roleResult" -ForegroundColor Gray
    }

} else {
    Write-Host "✅ Task 실행 성공!`n" -ForegroundColor Green

    # Task 정보 파싱
    try {
        $result = $output | ConvertFrom-Json

        if ($result.tasks.Count -gt 0) {
            $taskArn = $result.tasks[0].taskArn
            $taskId = $taskArn.Split('/')[-1]

            Write-Host "[2] Task 정보" -ForegroundColor Yellow
            Write-Host "  Task ID: $taskId" -ForegroundColor White
            Write-Host "  ARN: $taskArn" -ForegroundColor Gray
            Write-Host "  상태: $($result.tasks[0].lastStatus)" -ForegroundColor Gray
            Write-Host "`n  30초 후 로그 확인 권장:" -ForegroundColor Cyan
            Write-Host "  aws logs tail /ecs/scandeals-$testSite --since 2m --region $REGION" -ForegroundColor White
        }

        if ($result.failures.Count -gt 0) {
            Write-Host "`n[3] 실패 내역" -ForegroundColor Yellow
            foreach ($failure in $result.failures) {
                Write-Host "  ❌ $($failure.reason)" -ForegroundColor Red
                if ($failure.detail) {
                    Write-Host "     $($failure.detail)" -ForegroundColor Gray
                }
            }
        }
    }
    catch {
        Write-Host "JSON 파싱 실패, 그러나 명령은 성공적으로 실행됨" -ForegroundColor Yellow
    }
}

Write-Host "`n================================`n" -ForegroundColor Magenta