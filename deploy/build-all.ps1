﻿# ===== ���� =====
$SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")
$ECR_URL = "127679825681.dkr.ecr.ap-northeast-2.amazonaws.com"
$REPO_NAME = "scandeals-crawler"
# =================

Write-Host "[0/3] ECR �α��� �õ�..." -ForegroundColor Yellow
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin $ECR_URL
if ($LASTEXITCODE -ne 0) { Write-Host "[����] ECR �α��� ����" -ForegroundColor Red; return }
Write-Host "ECR �α��� ����!" -ForegroundColor Green

Write-Host "`n[1/3] Docker �̹��� ���带 �����մϴ�. (�� ${SITES.Count}��)" -ForegroundColor Cyan
foreach ($site in $SITES) {
    Write-Host "`n===== [$site] ���� ���� =====" -ForegroundColor Yellow
    $TAG_LOCAL = "$REPO_NAME`:$site"
    $TAG_ECR = "$ECR_URL/$REPO_NAME`:$site"
    
    # [������] deploy ���� ���� ��� ���
    $DOCKERFILE_PATH = "..\functions\$site\Dockerfile"

    # [������] ���� ���ؽ�Ʈ�� ��Ʈ ����(..)�� ����
    docker build -t $TAG_LOCAL -t $TAG_ECR -f $DOCKERFILE_PATH ..
    
    if ($LASTEXITCODE -ne 0) { Write-Host "[$site] ���� ����! �ߴ�." -ForegroundColor Red; return }
    Write-Host "[$site] ���� ����." -ForegroundColor Green
    
    Write-Host "===== [$site] ECR Ǫ�� ���� =====" -ForegroundColor Yellow
    docker push $TAG_ECR
    if ($LASTEXITCODE -ne 0) { Write-Host "[$site] Ǫ�� ����! �ߴ�." -ForegroundColor Red; return }
    Write-Host "[$site] ECR Ǫ�� ����!" -ForegroundColor Green
}
Write-Host "`n[3/3] ��� �۾� �Ϸ�! ??" -ForegroundColor Cyan
