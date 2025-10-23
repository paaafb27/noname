$ACCOUNT_ID = "127679825681"
$REGION = "ap-northeast-2"
$REPO = "scandeals-crawler"
$SITES = @("ppomppu", "ruliweb", "quasarzone", "arcalive", "eomisae", "fmkorea")

Write-Host "=== Step 1: IAM 역할 생성 ===" -ForegroundColor Yellow

# Trust Policy (BOM 없는 UTF-8)
$policy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

# BOM 없이 저장
[System.IO.File]::WriteAllText("$PWD\trust-policy.json", $policy, [System.Text.UTF8Encoding]::new($false))

# IAM 역할 생성
$roleExists = aws iam get-role --role-name scandeals-lambda-role 2>$null
if (-not $roleExists) {
    Write-Host "IAM 역할 생성 중..."
    aws iam create-role --role-name scandeals-lambda-role --assume-role-policy-document file://trust-policy.json

    Write-Host "권한 부여 중..."
    aws iam attach-role-policy --role-name scandeals-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    Write-Host "역할 전파 대기 (10초)..."
    Start-Sleep -Seconds 10
    Write-Host "IAM 역할 생성 완료" -ForegroundColor Green
} else {
    Write-Host "IAM 역할 이미 존재" -ForegroundColor Green
}

Write-Host "`n=== Step 2: Lambda 함수 6개 생성 ===" -ForegroundColor Yellow

foreach ($site in $SITES) {
    Write-Host "`n[$site] 생성 중..."

    $imageUri = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO`:$site"

    $result = aws lambda create-function --function-name "scandeals-$site" --package-type Image --code ImageUri=$imageUri --role "arn:aws:iam::$ACCOUNT_ID`:role/scandeals-lambda-role" --timeout 900 --memory-size 2048 --environment Variables="{API_URL=http://localhost:8080,API_KEY=test-key-for-development-only}" --region $REGION 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[$site] 생성 완료" -ForegroundColor Green
    } else {
        if ($result -like "*Function already exist*") {
            Write-Host "[$site] 이미 존재" -ForegroundColor Yellow
        } else {
            Write-Host "[$site] 생성 실패: $result" -ForegroundColor Red
        }
    }
}

Write-Host "`n=== Step 3: 생성 확인 ===" -ForegroundColor Yellow
aws lambda list-functions --query "Functions[?contains(FunctionName, 'scandeals')].FunctionName" --region $REGION

Write-Host "`n=== 완료 ===" -ForegroundColor Green