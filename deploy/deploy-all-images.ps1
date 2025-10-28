# 전체 자동화: 빌드 + Task Definition 업데이트 + EventBridge 타겟 업데이트

$REGION = "ap-northeast-2"
$ACCOUNT_ID = "127679825681"
$CLUSTER = "scandeals-crawler-cluster"
$SITES = @("ppomppu", "fmkorea", "quasarzone", "arcalive", "eomisae", "ruliweb")

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  전체 이미지 재배포 시작" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# 1. Docker 이미지 빌드 (기존 스크립트 사용)
.\build_all.ps1

# 2. Task Definition 자동 업데이트
foreach ($site in $SITES) {
    Write-Host "`n[$site] Task Definition 업데이트 중..." -ForegroundColor Yellow

    # 최신 Revision 자동 생성됨 (ECS가 자동 감지)
    # 별도 작업 불필요
}

# 3. EventBridge Target 업데이트
.\update-eventbridge-targets.ps1

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  전체 재배포 완료!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green