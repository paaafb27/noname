# ==================================================
# ECR 푸시 완전 자동화 스크립트
# ==================================================

# 1. AWS 계정 ID 자동 추출
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
Write-Host "AWS Account ID: $AWS_ACCOUNT_ID" -ForegroundColor Green

# 2. 리전 설정
$AWS_REGION = "ap-northeast-2"
$REPO_NAME = "scandeals-playwright-crawler"

# 3. ECR 리포지토리 생성 (이미 있으면 무시)
Write-Host "Creating ECR repository..." -ForegroundColor Yellow
aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION 2>$null

# 4. ECR URI 생성
$ECR_URI = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME"
Write-Host "ECR URI: $ECR_URI" -ForegroundColor Green

# 5. ECR 로그인
Write-Host "Logging in to ECR..." -ForegroundColor Yellow
$PASSWORD = aws ecr get-login-password --region $AWS_REGION
echo $PASSWORD | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

if ($LASTEXITCODE -eq 0) {
    Write-Host "ECR login successful!" -ForegroundColor Green
} else {
    Write-Host "ECR login failed!" -ForegroundColor Red
    exit 1
}

# 6. Docker 이미지 태그
Write-Host "Tagging Docker image..." -ForegroundColor Yellow
docker tag scandeals-playwright-crawler:latest ${ECR_URI}:latest

# 7. Docker 이미지 푸시
Write-Host "Pushing Docker image to ECR (10-20 minutes)..." -ForegroundColor Yellow
docker push ${ECR_URI}:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "Docker image pushed successfully!" -ForegroundColor Green
    Write-Host "ECR URI: $ECR_URI" -ForegroundColor Cyan
} else {
    Write-Host "Docker push failed!" -ForegroundColor Red
    exit 1
}

# 8. 푸시 확인
Write-Host "Verifying pushed image..." -ForegroundColor Yellow
aws ecr describe-images --repository-name $REPO_NAME --region $AWS_REGION

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "SUCCESS! Docker image pushed to ECR" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Next step: Create Lambda function with this URI:" -ForegroundColor Yellow
Write-Host "$ECR_URI:latest" -ForegroundColor White