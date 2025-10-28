$REGION = "ap-northeast-2"
$CLUSTER = "scandeals-crawler-cluster"
$ACCOUNT_ID = "127679825681"
$SITES = @("ppomppu", "fmkorea", "quasarzone", "arcalive", "eomisae", "ruliweb")

$SUBNETS = @(
    "subnet-0cf0b2476d85e7adb",
    "subnet-0bcb51270debe69d6",
    "subnet-0d1bac072b236398b",
    "subnet-04352f96229a481ac"
)
$SECURITY_GROUP = "sg-06b877fb23276fcbf"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  EventBridge Target 업데이트" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

foreach ($site in $SITES) {
    $ruleName = "scandeals-$site-schedule"
    $taskDefinition = "scandeals-$site"

    Write-Host "[$site] 업데이트 중..." -ForegroundColor Yellow

    # 1. 기존 Target 제거
    aws events remove-targets `
      --rule $ruleName `
      --ids "1" `
      --region $REGION 2>&1 | Out-Null

    # 2. 최신 Task Definition ARN 가져오기
    $taskDefArn = aws ecs describe-task-definition `
      --task-definition $taskDefinition `
      --region $REGION `
      --query "taskDefinition.taskDefinitionArn" `
      --output text

    # 3. Target JSON 파일 생성
    $targetFile = "target-$site.json"
    $targetJson = @"
[
  {
    "Id": "1",
    "Arn": "arn:aws:ecs:${REGION}:${ACCOUNT_ID}:cluster/${CLUSTER}",
    "RoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/ecsEventsRole",
    "EcsParameters": {
      "TaskDefinitionArn": "${taskDefArn}",
      "TaskCount": 1,
      "LaunchType": "FARGATE",
      "NetworkConfiguration": {
        "awsvpcConfiguration": {
          "Subnets": [
            "subnet-0cf0b2476d85e7adb",
            "subnet-0bcb51270debe69d6",
            "subnet-0d1bac072b236398b",
            "subnet-04352f96229a481ac"
          ],
          "SecurityGroups": ["${SECURITY_GROUP}"],
          "AssignPublicIp": "ENABLED"
        }
      }
    }
  }
]
"@

    $targetJson | Out-File -FilePath $targetFile -Encoding ASCII -NoNewline

    # 4. Target 추가
    aws events put-targets `
      --rule $ruleName `
      --targets file://$targetFile `
      --region $REGION 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 완료`n" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 실패`n" -ForegroundColor Red
    }

    Remove-Item $targetFile -ErrorAction SilentlyContinue
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  업데이트 완료!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green