# view-logs.ps1
# Lambda 로그 조회 스크립트 (인코딩 문제 해결)

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb", "all")]
    [string]$Site,
    
    [Parameter(Mandatory=$false)]
    [int]$Lines = 30,
    
    [Parameter(Mandatory=$false)]
    [string]$Since = "30m"
)

$ErrorActionPreference = "SilentlyContinue"
$REGION = "ap-northeast-2"

# 출력 인코딩을 UTF-8로 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Get-LambdaLogs {
    param(
        [string]$SiteName
    )
    
    Write-Host "`n" + "="*70 -ForegroundColor Cyan
    Write-Host "[$SiteName] 최근 로그 (최근 $Since, 마지막 $Lines 줄)" -ForegroundColor Cyan
    Write-Host "="*70 -ForegroundColor Cyan
    
    $logGroup = "/aws/lambda/scandeals-$SiteName"
    
    # AWS CLI 출력을 UTF-8로 받기
    $env:PYTHONIOENCODING = "utf-8"
    
    # 로그 가져오기
    $logs = aws logs tail $logGroup `
        --since $Since `
        --format short `
        --region $REGION 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 로그 조회 실패: $logs" -ForegroundColor Red
        return
    }
    
    # 마지막 N줄만 출력
    $logLines = $logs -split "`n"
    $lastLines = $logLines | Select-Object -Last $Lines
    
    foreach ($line in $lastLines) {
        # 한글 깨짐 방지를 위해 바이트 배열로 변환 후 UTF-8로 디코딩
        try {
            Write-Host $line
        } catch {
            Write-Host $line -NoNewline
        }
    }
    
    Write-Host ""
}

if ($Site -eq "all") {
    $SITES = @("arcalive", "eomisae", "fmkorea", "ppomppu", "quasarzone", "ruliweb")
    foreach ($s in $SITES) {
        Get-LambdaLogs -SiteName $s
        Start-Sleep -Seconds 1
    }
} else {
    Get-LambdaLogs -SiteName $Site
}