# ================== 최종 완성 스크립트 (v2) ==================

# ECR 설정
$ACCOUNT_ID = "127679825681"
$REGION = "ap-northeast-2"
$REPO_NAME = "scandeals-crawler"
$SITES = @("ppomppu", "ruliweb", "quasarzone", "arcalive", "eomisae", "fmkorea")

# (선택 사항) 스크립트 시작 시 기존 ECR 이미지 삭제
Write-Host "기존 ECR 이미지 삭제 중..."
foreach ($site in $SITES) {
    aws ecr batch-delete-image --repository-name $REPO_NAME --image-ids imageTag=$site --region $REGION 2>$null
}

# ECR 로그인
Write-Host "ECR 로그인..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ECR 로그인 실패!" -ForegroundColor Red
    exit 1
}

# --- 여기가 핵심: 빌드 컨텍스트를 프로젝트 루트로 설정 ---
Set-Location "F:\scandeals-crawler"

try {
    # 각 사이트 빌드 및 푸시
    foreach ($site in $SITES) {
        Write-Host "`n[$site] 빌드 시작..."

        # 최종 ECR 이미지 URI 정의
        $IMAGE_URI = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${site}"

        # Dockerfile 및 관련 파일 경로 정의
        $SITE_PATH_ARG = "functions/${site}"

        # --- 올바른 Docker Build 명령어 ---
        docker build -t $IMAGE_URI --platform linux/amd64 --build-arg SITE_PATH=${SITE_PATH_ARG} -f "${SITE_PATH_ARG}/Dockerfile" .
        
        if ($LASTEXITCODE -ne 0) {
            throw "[$site] Docker 빌드 실패!"
        }
        
        Write-Host "[$site] 빌드 성공"
        
        # 푸시
        Write-Host "[$site] ECR 푸시..."
        docker push $IMAGE_URI
        if ($LASTEXITCODE -ne 0) {
            throw "[$site] Docker 푸시 실패!"
        }

        Write-Host "[$site] 푸시 완료"
    }
}
catch {
    Write-Host "`n작업 중단:" -ForegroundColor Red
    Write-Host $_ -ForegroundColor Red
}
finally {
    # 스크립트가 끝나면 원래 디렉토리로 복귀 (매우 중요)
    Set-Location "F:\scandeals-crawler\deploy"
    Write-Host "`n모든 작업 완료!"
}