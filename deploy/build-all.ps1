# ===== 설정 =====
$SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")
$ECR_URL = "127679825681.dkr.ecr.ap-northeast-2.amazonaws.com"
$REPO_NAME = "scandeals-crawler"
# =================

Write-Host "[0/3] ECR 로그인 시도..." -ForegroundColor Yellow
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin $ECR_URL
if ($LASTEXITCODE -ne 0) { Write-Host "[오류] ECR 로그인 실패" -ForegroundColor Red; return }
Write-Host "ECR 로그인 성공!" -ForegroundColor Green

Write-Host "`n[1/3] Docker 이미지 빌드를 시작합니다. (총 ${SITES.Count}개)" -ForegroundColor Cyan
foreach ($site in $SITES) {
    Write-Host "`n===== [$site] 빌드 시작 =====" -ForegroundColor Yellow
    $TAG_LOCAL = "$REPO_NAME`:$site"
    $TAG_ECR = "$ECR_URL/$REPO_NAME`:$site"
    
    # [수정됨] deploy 폴더 기준 상대 경로
    $DOCKERFILE_PATH = "..\functions\$site\Dockerfile"

    # [수정됨] 빌드 컨텍스트를 루트 폴더(..)로 지정
    docker build -t $TAG_LOCAL -t $TAG_ECR -f $DOCKERFILE_PATH ..
    
    if ($LASTEXITCODE -ne 0) { Write-Host "[$site] 빌드 실패! 중단." -ForegroundColor Red; return }
    Write-Host "[$site] 빌드 성공." -ForegroundColor Green
    
    Write-Host "===== [$site] ECR 푸시 시작 =====" -ForegroundColor Yellow
    docker push $TAG_ECR
    if ($LASTEXITCODE -ne 0) { Write-Host "[$site] 푸시 실패! 중단." -ForegroundColor Red; return }
    Write-Host "[$site] ECR 푸시 성공!" -ForegroundColor Green
}
Write-Host "`n[3/3] 모든 작업 완료! ??" -ForegroundColor Cyan
