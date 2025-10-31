# 크롤러 통합 테스트 PowerShell 스크립트
# 사용법: .\test_crawlers.ps1 [사이트명...]

param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Sites,
    
    [int]$Minutes = 120,
    [switch]$NoSave,
    [switch]$List
)

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "크롤러 통합 테스트 스크립트" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Python 및 패키지 확인
Write-Host "환경 확인 중..." -ForegroundColor Yellow

# 필요한 패키지 설치
$packages = @(
    "selenium",
    "beautifulsoup4",
    "lxml",
    "webdriver-manager",
    "requests"
)

Write-Host "필요한 패키지 설치 확인..." -ForegroundColor Yellow
foreach ($pkg in $packages) {
    pip show $pkg > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  설치: $pkg" -ForegroundColor Gray
        pip install $pkg --quiet
    }
}

Write-Host "✅ 환경 확인 완료" -ForegroundColor Green
Write-Host ""

# Python 스크립트 실행
$pythonArgs = @("test_crawlers.py")

# 사이트 인자 추가
if ($Sites) {
    $pythonArgs += $Sites
}

# 필터링 시간 추가
if ($Minutes -ne 120) {
    $pythonArgs += "--minutes"
    $pythonArgs += $Minutes
}

# JSON 저장 옵션
if ($NoSave) {
    $pythonArgs += "--no-save"
}

# 목록 출력
if ($List) {
    $pythonArgs += "--list"
}

# 실행
Write-Host "크롤러 테스트 실행 중..." -ForegroundColor Green
Write-Host ""

python @pythonArgs

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "테스트 완료" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 사용 예제 출력
if ($LASTEXITCODE -ne 0) {
    Write-Host "사용 예제:" -ForegroundColor Yellow
    Write-Host "  .\test_crawlers.ps1                      # 모든 사이트 테스트" -ForegroundColor Gray
    Write-Host "  .\test_crawlers.ps1 ppomppu              # 뽐뿌만 테스트" -ForegroundColor Gray
    Write-Host "  .\test_crawlers.ps1 ppomppu ruliweb      # 여러 사이트 테스트" -ForegroundColor Gray
    Write-Host "  .\test_crawlers.ps1 -Minutes 60          # 60분 필터링" -ForegroundColor Gray
    Write-Host "  .\test_crawlers.ps1 -NoSave              # JSON 저장 안함" -ForegroundColor Gray
    Write-Host "  .\test_crawlers.ps1 -List                # 지원 사이트 목록" -ForegroundColor Gray
    Write-Host ""
}
