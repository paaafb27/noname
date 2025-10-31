@echo off
REM ###############################################################################
REM 개별 크롤러 로컬 테스트 스크립트 (Windows)
REM 
REM 목적: 특정 크롤러를 Docker로 빌드하고 로컬에서 테스트
REM 사용법: test-crawler.bat ppomppu
REM ###############################################################################

setlocal

REM 인자 확인
if "%~1"=="" (
    echo [ERROR] 사용법: %0 ^<crawler_name^>
    echo 예시: %0 ppomppu
    echo.
    echo 사용 가능한 크롤러:
    echo   - ppomppu
    echo   - ruliweb
    echo   - fmkorea
    echo   - quasarzone
    echo   - arcalive
    echo   - eomisae
    exit /b 1
)

set CRAWLER_NAME=%~1
set DOCKERFILE_PATH=functions\%CRAWLER_NAME%\Dockerfile
set IMAGE_TAG=%CRAWLER_NAME%-crawler:local

REM API 엔드포인트 설정
if not defined API_ENDPOINT (
    set API_ENDPOINT=http://host.docker.internal:8080
)

REM 필터링 시간
if not defined FILTER_MINUTES (
    set FILTER_MINUTES=30
)

REM Dockerfile 존재 확인
if not exist "%DOCKERFILE_PATH%" (
    echo [ERROR] Dockerfile 없음: %DOCKERFILE_PATH%
    exit /b 1
)

echo =====================================
echo   %CRAWLER_NAME% 크롤러 테스트
echo =====================================
echo.
echo Dockerfile: %DOCKERFILE_PATH%
echo 이미지 태그: %IMAGE_TAG%
echo API 엔드포인트: %API_ENDPOINT%
echo 필터링 시간: %FILTER_MINUTES%분
echo.

REM 1. Docker 이미지 빌드
echo [1/2] Docker 이미지 빌드 중...
docker build -f "%DOCKERFILE_PATH%" -t "%IMAGE_TAG%" .
if %errorlevel% neq 0 (
    echo [ERROR] 빌드 실패
    exit /b 1
)
echo [OK] 빌드 성공
echo.

REM 2. Docker 컨테이너 실행
echo [2/2] 크롤러 실행 중...
echo.
docker run --rm -e API_ENDPOINT="%API_ENDPOINT%" -e FILTER_MINUTES=%FILTER_MINUTES% "%IMAGE_TAG%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 실행 실패
    exit /b 1
)

echo.
echo [OK] 크롤러 실행 완료
exit /b 0
