# deploy-and-test.ps1

# --- 설정 ---
# 여기에 배포하고 테스트할 사이트 목록을 입력하세요.
$TARGET_SITES = @("ruliweb", "ppomppu", "arcalive", "fmkorea", "eomisae", "quasarzone" )

$REGION = "ap-northeast-2"

# --- 스크립트 시작 ---
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ROOT_DIR = "F:\scandeals-crawler" # 프로젝트 루트 경로 (필요시 수정)

# 공통 모듈 경로 확인
$COMMON_MODULE_DIR = Join-Path $ROOT_DIR "common"
if (-not (Test-Path $COMMON_MODULE_DIR)) {
    Write-Host "❌ 공통 모듈 폴더를 찾을 수 없습니다: $COMMON_MODULE_DIR" -ForegroundColor Red
    exit 1
}

Write-Host "`n🚀 선택된 사이트 배포 및 테스트 시작: $($TARGET_SITES -join ', ')`n" -ForegroundColor Cyan

# 각 사이트에 대해 배포 및 테스트 실행
foreach ($site in $TARGET_SITES) {
    $functionDir = Join-Path $ROOT_DIR "functions\$site"
    $functionName = "scandeals-$site"
    $zipFile = "$site-lambda-package.zip"

    # --- 1. 배포 ---
    Write-Host "--- [$site] 배포 시작 ---" -ForegroundColor Yellow

    if (-not (Test-Path $functionDir)) {
        Write-Host "  ❌ '$site' 함수 폴더를 찾을 수 없습니다. 건너뜁니다." -ForegroundColor Red
        continue
    }

    # 이전 압축 파일 삭제
    if (Test-Path $zipFile) {
        Remove-Item $zipFile
    }

    # [수정] PowerShell 내장 기능으로 압축
    try {
        # 압축할 파일/폴더 목록을 배열로 만듭니다.
        $filesToCompress = @(
            (Get-ChildItem -Path $functionDir -Recurse).FullName
            (Get-ChildItem -Path $COMMON_MODULE_DIR -Recurse).FullName
    )
    # 압축 실행
        Compress-Archive -Path $filesToCompress -DestinationPath $zipFile -Force
        Write-Host "  📦 압축 완료: $zipFile"
    } catch {
        Write-Host "  ❌ PowerShell 압축 실패: $($_.Exception.Message)" -ForegroundColor Red
        continue
    }

    # Lambda 함수 코드 업데이트
    Write-Host "  ☁️ '$functionName' 함수에 코드 업로드 중..."
    $updateResult = aws lambda update-function-code --function-name $functionName --zip-file "fileb://$zipFile" --region $REGION --output json

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 배포 성공!" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 배포 실패!" -ForegroundColor Red
        Write-Host $updateResult
    }

    # 임시 압축 파일 삭제
    Remove-Item $zipFile

    # --- 2. 테스트 실행 (Invoke) ---
    Write-Host "\n  ▶️ [$site] 테스트 실행 시작..." -ForegroundColor Yellow
    $responseFile = "$site-response.json"

    aws lambda invoke --function-name $functionName --region $REGION $responseFile

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 실행 요청 성공! (StatusCode: 200)" -ForegroundColor Green
        Write-Host "  📄 응답 확인:"
        # cat 명령어는 PowerShell Core (pwsh.exe) 에서는 잘 동작하지만, Windows PowerShell 에서는 깨질 수 있습니다.
        # Get-Content를 사용하여 더 안정적으로 출력합니다.
        Get-Content $responseFile -Raw
    } else {
        Write-Host "  ❌ 실행 요청 실패!" -ForegroundColor Red
    }

    # --- 3. 로그 확인 ---
    Write-Host "\n  📜 [$site] 최신 로그 확인 (지난 2분)..." -ForegroundColor Yellow
    # --format short 옵션으로 간결하게 출력
    aws logs tail "/aws/lambda/$functionName" --since 2m --format short --region $REGION --output text | Select-Object -Last 15

    Write-Host "---------------------------------`n"
}

Write-Host "✨ 모든 작업 완료! ✨`n" -ForegroundColor Cyan