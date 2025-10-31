@echo off
REM ###############################################################################
REM 전체 크롤러 로컬 테스트 스크립트 (Windows)
REM 
REM 목적: 모든 크롤러를 Docker로 빌드하고 로컬에서 테스트
REM 사용법: test-all-crawlers.bat
REM ###############################################################################

setlocal EnableDelayedExpansion

REM API 엔드포인트 설정
if not defined API_ENDPOINT (
    set API_ENDPOINT=http://host.docker.internal:8080
)

REM 크롤러 목록
set CRAWLERS=ppomppu ruliweb fmkorea quasarzone arcalive eomisae

REM 결과 카운터
set SUCCESS_COUNT=0
set FAIL_COUNT=0

echo =====================================
echo   전체 크롤러 로컬 테스트 시작
echo =====================================
echo.
echo API 엔드포인트: %API_ENDPOINT%
echo.

REM 시작 시간
set START_TIME=%time%

REM 각 크롤러 테스트
for %%C in (%CRAWLERS%) do (
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo [%time%] 테스트 중: %%C
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    set DOCKERFILE_PATH=functions\%%C\Dockerfile
    set IMAGE_TAG=%%C-crawler:local
    
    REM Dockerfile 존재 확인
    if not exist "!DOCKERFILE_PATH!" (
        echo [ERROR] Dockerfile 없음: !DOCKERFILE_PATH!
        set /a FAIL_COUNT+=1
        goto :next_crawler
    )
    
    REM Docker 이미지 빌드
    echo [BUILD] Docker 이미지 빌드 중...
    docker build -f "!DOCKERFILE_PATH!" -t "!IMAGE_TAG!" . > %TEMP%\%%C_build.log 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] 빌드 실패
        type %TEMP%\%%C_build.log | more /E +50
        set /a FAIL_COUNT+=1
        goto :next_crawler
    )
    echo [OK] 빌드 성공
    
    REM Docker 컨테이너 실행
    echo [RUN] 크롤러 실행 중...
    docker run --rm -e API_ENDPOINT="%API_ENDPOINT%" -e FILTER_MINUTES=30 "!IMAGE_TAG!" > %TEMP%\%%C_run.log 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] 실행 실패
        type %TEMP%\%%C_run.log | more /E +50
        set /a FAIL_COUNT+=1
        goto :next_crawler
    )
    
    REM 결과 확인
    findstr /C:"크롤링 완료" /C:"총.*개 수집" %TEMP%\%%C_run.log > nul
    if !errorlevel! equ 0 (
        echo [OK] 실행 성공
        
        REM 수집 개수 출력
        for /f "tokens=2 delims= " %%N in ('findstr /R "총.*개 수집" %TEMP%\%%C_run.log') do (
            echo [INFO] 수집 개수: %%N
        )
        
        set /a SUCCESS_COUNT+=1
    ) else (
        echo [ERROR] 실행 실패 (예상 출력 없음)
        type %TEMP%\%%C_run.log | more /E +50
        set /a FAIL_COUNT+=1
    )
    
    :next_crawler
)

REM 종료 시간
set END_TIME=%time%

echo.
echo =====================================
echo   테스트 결과 요약
echo =====================================
echo.
echo 성공: %SUCCESS_COUNT%개
echo 실패: %FAIL_COUNT%개
echo.

if %FAIL_COUNT% gtr 0 (
    echo [ERROR] 일부 크롤러 테스트 실패
    exit /b 1
) else (
    echo [OK] 모든 크롤러 테스트 성공!
    exit /b 0
)
