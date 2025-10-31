# EventBridge 스케줄 설정 (수정본)


$ACCOUNT_ID = "127679825681"
$REGION = "ap-northeast-2"
$CLUSTER = "scandeals-crawler-cluster"
$SUBNET_ID = "subnet-0cf0b2476d85e7adb"
$SG_ID = "sg-06b877fb23276fcbf"
$SITES = @("ruliweb", "quasarzone", "arcalive", "eomisae", "fmkorea")


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

Write-Host "================================" -ForegroundColor Magenta
Write-Host "EventBridge 스케줄 설정" -ForegroundColor Magenta
Write-Host "================================`n" -ForegroundColor Magenta

# Subnet과 SG 설정 확인
if ($SUBNET_ID -eq "subnet-xxxxxxxxx" -or $SG_ID -eq "sg-xxxxxxxxx") {
    Write-Host "❌ 오류: SUBNET_ID와 SG_ID를 실제 값으로 변경해주세요`n" -ForegroundColor Red

    Write-Host "1. VPC Public Subnet 조회:" -ForegroundColor Yellow
    Write-Host "aws ec2 describe-subnets --region $REGION --query 'Subnets[?MapPublicIpOnLaunch==``true``].[SubnetId,AvailabilityZone,CidrBlock]' --output table`n" -ForegroundColor Cyan

    Write-Host "2. Security Group 조회:" -ForegroundColor Yellow
    Write-Host "aws ec2 describe-security-groups --region $REGION --query 'SecurityGroups[*].[GroupId,GroupName,Description]' --output table`n" -ForegroundColor Cyan

    Write-Host "3. 또는 기본 VPC 사용 시:" -ForegroundColor Yellow
    Write-Host "aws ec2 describe-subnets --region $REGION --filters 'Name=default-for-az,Values=true' --query 'Subnets[0].SubnetId' --output text`n" -ForegroundColor Cyan

    exit 1
}

# IAM Role 확인
Write-Host "[사전 확인] IAM Role 존재 여부" -ForegroundColor Yellow
$roleCheck = aws iam get-role --role-name ecsEventsRole --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ⚠️  ecsEventsRole이 없습니다. 생성합니다..." -ForegroundColor Yellow

    # Trust Policy
    $trustPolicy = @"
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
"@
    $trustPolicy | Out-File -FilePath "trust-policy.json" -Encoding UTF8 -NoNewline

    # Role 생성
    aws iam create-role `
        --role-name ecsEventsRole `
        --assume-role-policy-document file://trust-policy.json `
        --region $REGION | Out-Null

    # Policy 연결
    aws iam attach-role-policy `
        --role-name ecsEventsRole `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceEventsRole" `
        --region $REGION | Out-Null

    Remove-Item "trust-policy.json"
    Write-Host "  ✅ ecsEventsRole 생성 완료`n" -ForegroundColor Green

    # Role 전파 대기
    Write-Host "  Role 전파 대기 (10초)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
} else {
    Write-Host "  ✅ ecsEventsRole 존재`n" -ForegroundColor Green
}

# EventBridge Rule 및 Target 생성
foreach ($site in $SITES) {
    $ruleName = "scandeals-${site}-schedule"

    Write-Host "[$site] EventBridge Rule 생성..." -ForegroundColor Yellow

    # Rule 생성 (10분마다)
    aws events put-rule `
        --name $ruleName `
        --schedule-expression "rate(10 minutes)" `
        --state ENABLED `
        --description "scandeals $site crawler - every 10 minutes" `
        --region $REGION | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Rule 생성 완료" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Rule 생성 실패" -ForegroundColor Red
        continue
    }

    # Target JSON 생성
    $targetJson = @"
[
  {
    "Id": "1",
    "Arn": "arn:aws:ecs:${REGION}:${ACCOUNT_ID}:cluster/${CLUSTER}",
    "RoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/ecsEventsRole",
    "EcsParameters": {
      "TaskDefinitionArn": "arn:aws:ecs:${REGION}:${ACCOUNT_ID}:task-definition/scandeals-${site}",
      "TaskCount": 1,
      "LaunchType": "FARGATE",
      "NetworkConfiguration": {
        "awsvpcConfiguration": {
          "Subnets": ["${SUBNET_ID}"],
          "SecurityGroups": ["${SG_ID}"],
          "AssignPublicIp": "ENABLED"
        }
      }
    }
  }
]
"@

    # UTF-8 인코딩으로 저장
    $targetJson | Out-File -FilePath "target-$site.json" -Encoding UTF8 -NoNewline

    # Target 설정
    aws events put-targets `
        --rule $ruleName `
        --targets file://target-$site.json `
        --region $REGION | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Target 설정 완료" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Target 설정 실패" -ForegroundColor Red
        Write-Host "     JSON 파일 확인: target-$site.json" -ForegroundColor Yellow
        continue
    }

    # 임시 파일 삭제
    Remove-Item "target-$site.json" -ErrorAction SilentlyContinue
}

Write-Host "`n================================" -ForegroundColor Magenta
Write-Host "✅ 모든 스케줄 설정 완료!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Magenta

Write-Host "`n다음 실행 시간: 현재부터 10분 후" -ForegroundColor Cyan
Write-Host "10분 후 로그 확인:" -ForegroundColor White
Write-Host @"
foreach (`$site in @("ruliweb", "quasarzone", "arcalive", "eomisae", "fmkorea")) {
    Write-Host "`n[`$site] 최근 로그:" -ForegroundColor Cyan
    aws logs tail "/ecs/scandeals-`$site" --since 5m --region $REGION
}
"@ -ForegroundColor Cyan

Write-Host "`n또는 즉시 수동 테스트:" -ForegroundColor White
Write-Host ".\run-task-manual-test.ps1`n" -ForegroundColor Cyan