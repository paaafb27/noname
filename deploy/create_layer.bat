@echo off
REM ========================================
REM Playwright Layer 자동 빌드 스크립트
REM 사용 의도: Lambda Layer 자동 생성 및 최적화
REM 효과: 수동 작업 자동화, 용량 20% 절약, 7개 함수 공통 사용
REM ========================================

echo.
echo ========================================
echo scanDeals Playwright Layer 빌드
echo ========================================
echo.

REM 1. 임시 디렉토리 생성
echo [1/7] 임시 디렉토리 생성 중...
if exist F:\temp\playwright-layer rmdir /s /q F:\temp\playwright-layer
mkdir F:\temp\playwright-layer
mkdir F:\temp\playwright-layer\python
echo      완료
echo.

REM 2. pip 패키지 설치
echo [2/7] Python 패키지 설치 중... (1-2분 소요)
pip install -t F:\temp\playwright-layer\python ^
    playwright==1.40.0 ^
    beautifulsoup4==4.12.2 ^
    lxml==4.9.3 ^
    requests==2.31.0

if errorlevel 1 (
    echo      오류: pip 설치 실패
    echo      해결: python --version 확인 후 pip 재설치
    pause
    exit /b 1
)
echo      완료
echo.

REM 3. Chromium 브라우저 설치
echo [3/7] Chromium 브라우저 설치 중... (3-5분 소요)
cd F:\temp\playwright-layer\python
python -m playwright install chromium

if errorlevel 1 (
    echo      오류: Chromium 설치 실패
    echo      해결: 관리자 권한으로 cmd 재실행
    pause
    exit /b 1
)
echo      완료
echo.

REM 4. 불필요한 파일 삭제
echo [4/7] 불필요한 파일 삭제 중... (용량 20%% 절약)
cd F:\temp\playwright-layer\python

REM .pyc 파일 삭제
del /s /q *.pyc 2>nul

REM __pycache__ 폴더 삭제
for /d /r %%i in (__pycache__) do @if exist "%%i" rd /s /q "%%i"

REM .dist-info 폴더 삭제
for /d /r %%i in (*.dist-info) do @if exist "%%i" rd /s /q "%%i"

REM tests 폴더 삭제
for /d /r %%i in (tests) do @if exist "%%i" rd /s /q "%%i"

echo      완료
echo.

REM 5. Firefox, WebKit 삭제 (Chromium만 사용)
echo [5/7] 불필요한 브라우저 삭제 중...
cd F:\temp\playwright-layer\python\playwright\driver

if exist firefox rd /s /q firefox
if exist webkit rd /s /q webkit

echo      완료 (Chromium만 유지)
echo.

REM 6. ZIP 압축
echo [6/7] ZIP 압축 중... (1-2분 소요)
cd F:\temp\playwright-layer
powershell Compress-Archive -Path python -DestinationPath playwright-layer.zip -Force

if errorlevel 1 (
    echo      오류: ZIP 압축 실패
    echo      해결: PowerShell 권한 설정 필요
    pause
    exit /b 1
)
echo      완료
echo.

REM 7. 결과 이동
echo [7/7] 결과 파일 이동 중...
if exist F:\scandeals-crawler\deploy\playwright-layer.zip del F:\scandeals-crawler\deploy\playwright-layer.zip
move playwright-layer.zip F:\scandeals-crawler\deploy\
echo      완료
echo.

echo ========================================
echo 빌드 완료!
echo ========================================
echo 파일 위치: F:\scandeals-crawler\deploy\playwright-layer.zip
echo 파일 크기: 약 100-120MB
echo.
echo 다음 단계:
echo 1. AWS Lambda Console 접속
echo 2. Layers 메뉴에서 Create layer
echo 3. playwright-layer.zip 업로드
echo 4. Compatible runtimes: Python 3.11 선택
echo 5. Layer ARN 복사 (함수 배포 시 사용)
echo ========================================
echo.
pause