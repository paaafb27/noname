# ==========================================
# EventBridge Scheduler for Fargate (최종 버전)
# JSON 직접 작성 방식
# ==========================================

$REGION = "ap-northeast-2"
$ACCOUNT_ID = "127679825681"
$CLUSTER_NAME = "scandeals-crawler-cluster"
$SITES = @("ppomppu", "fmkorea", "quasarzone", "arcalive", "eomisae", "ruliweb")

# 서브넷
$SUBNET1 = "subnet-0cf0b2476d85e7adb"
$SUBNET2 = "subnet-0bcb51270debe69d6"
$SUBNET3 = "subnet-0d1bac072b236398b"
$SUBNET4 = "subnet-04352f96229a481ac"

$SECURITY_GROUP = "sg-06b877fb23276fcbf"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  EventBridge Scheduler 설정" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# ecsEventsRole 확인
Write-Host "ecsEventsRole 확인 중..." -ForegroundColor Yellow
$roleCheck = aws iam get-role --role-name ecsEventsRole --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ecsEventsRole 생성 중..." -ForegroundColor Yellow

    $trustPolicy = @'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
'@

    $trustPolicy | Out-File -FilePath "trust-policy.json" -Encoding ASCII -NoNewline

    aws iam create-role `
        --role-name ecsEventsRole `
        --assume-role-policy-document file://trust-policy.json | Out-Null

    aws iam attach-role-policy `
        --role-name ecsEventsRole `
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceEventsRole | Out-Null

    Remove-Item "trust-policy.json" -ErrorAction SilentlyContinue
    Write-Host "ecsEventsRole 생성 완료`n" -ForegroundColor Green
} else {
    Write-Host "ecsEventsRole 이미 존재`n" -ForegroundColor Green
}

foreach ($site in $SITES) {
    $ruleName = "scandeals-$site-schedule"
    $taskDefinition = "scandeals-$site"

    Write-Host "[$site] 스케줄 생성 중..." -ForegroundColor Yellow

    # 1. EventBridge Rule 생성 (10분마다)
    Write-Host "  Rule 생성..." -ForegroundColor Gray
    aws events put-rule `
        --name $ruleName `
        --schedule-expression "rate(10 minutes)" `
        --state ENABLED `
        --region $REGION | Out-Null

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Rule 생성 실패`n" -ForegroundColor Red
        continue
    }

    # 2. Target JSON 직접 작성 (AWS CLI 형식)
    $targetJson = @"
[
  {
    "Id": "1",
    "Arn": "arn:aws:ecs:${REGION}:${ACCOUNT_ID}:cluster/${CLUSTER_NAME}",
    "RoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/ecsEventsRole",
    "EcsParameters": {
      "TaskDefinitionArn": "arn:aws:ecs:${REGION}:${ACCOUNT_ID}:task-definition/${taskDefinition}",
      "TaskCount": 1,
      "LaunchType": "FARGATE",
      "NetworkConfiguration": {
        "awsvpcConfiguration": {
          "Subnets": [
            "${SUBNET1}",
            "${SUBNET2}",
            "${SUBNET3}",
            "${SUBNET4}"
          ],
          "SecurityGroups": [
            "${SECURITY_GROUP}"
          ],
          "AssignPublicIp": "ENABLED"
        }
      }
    }
  }
]
"@

    # 파일로 저장 (ASCII 인코딩)
    $targetFile = "target-$site.json"
    $targetJson | Out-File -FilePath $targetFile -Encoding ASCII -NoNewline

    Write-Host "  Target 연결 중..." -ForegroundColor Gray
    $putResult = aws events put-targets `
        --rule $ruleName `
        --targets file://$targetFile `
        --region $REGION 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 완료`n" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 실패: $putResult`n" -ForegroundColor Red
    }

    # 임시 파일 삭제
    Remove-Item $targetFile -ErrorAction SilentlyContinue
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  EventBridge 설정 완료!" -ForegroundColor Green
Write-Host "  10분마다 자동 실행됩니다." -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# 확인
Write-Host "생성된 스케줄:" -ForegroundColor Cyan
aws events list-rules --name-prefix scandeals --region $REGION --query "Rules[].Name" --output table

Write-Host "`nppomppu Target 상세:" -ForegroundColor Cyan
aws events list-targets-by-rule --rule scandeals-ppomppu-schedule --region $REGION