# 뽐뿌 크롤러 실행 스크립트 (scandeals-crawler 구조용)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 뽐뿌 크롤러 실행" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 현재 위치 확인
Write-Host "📍 현재 디렉토리:" -ForegroundColor Yellow
Get-Location
Write-Host ""

# 루트 디렉토리로 이동 (deploy에서 실행 시)
if ((Get-Location).Path -like "*\deploy") {
    Write-Host "📂 루트 디렉토리로 이동..." -ForegroundColor Yellow
    Set-Location ..
    Write-Host ""
}

# 크롤러 파일 확인
$scraperPath = "functions\ppomppu\scraper.py"
if (-not (Test-Path $scraperPath)) {
    Write-Host "❌ 파일 없음: $scraperPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "현재 디렉토리 구조:" -ForegroundColor Yellow
    Get-ChildItem -Directory | Select-Object Name
    exit 1
}

Write-Host "✅ 크롤러 파일 확인: $scraperPath" -ForegroundColor Green
Write-Host ""

# Python 버전 확인
Write-Host "📍 Python 버전:" -ForegroundColor Yellow
python --version
Write-Host ""

# PYTHONPATH 설정 (common 모듈 인식용)
$env:PYTHONPATH = (Get-Location).Path
Write-Host "📦 PYTHONPATH 설정: $env:PYTHONPATH" -ForegroundColor Yellow
Write-Host ""

# 크롤러 실행
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔄 크롤러 실행 시작..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# functions/ppomppu/scraper.py 실행
Set-Location functions\ppomppu
python scraper.py
$exitCode = $LASTEXITCODE
Set-Location ..\..

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "✅ 크롤러 실행 성공!" -ForegroundColor Green
} else {
    Write-Host "❌ 크롤러 실행 실패 (exit code: $exitCode)" -ForegroundColor Red
}
Write-Host "============================================================" -ForegroundColor Cyan