#Requires -Version 5.1

<#
.SYNOPSIS
    Fargate 크롤러 전체 테스트 스크립트 (PowerShell)

.DESCRIPTION
    모든 크롤러를 Fargate에서 실행하고 결과를 수집합니다.
    - ECS Task 실행
    - 로그 수집 (CloudWatch Logs)
    - 결과 요약
    
.PARAMETER Region
    AWS 리전 (기본값: ap-northeast-2)
    
.PARAMETER ClusterName
    ECS 클러스터 이름 (기본값: scandeals-crawler-cluster)
    
.PARAMETER WaitMinutes
    Task 완료 대기 시간 (분, 기본값: 5)
    
.EXAMPLE
    .\Test-FargateCrawlers.ps1
    
.EXAMPLE
    .\Test-FargateCrawlers.ps1 -Region ap-northeast-2 -WaitMinutes 3
#>

[CmdletBinding()]
param(
    [string]$Region = "ap-northeast-2",
    [string]$ClusterName = "scandeals-crawler-cluster",
    [int]$WaitMinutes = 5,
    [string]$SubnetId = "",  # 필수: 본인의 Subnet ID
    [string]$SecurityGroupId = ""  # 필수: 본인의 Security Group ID
)

# 색상 설정
$script:SuccessColor = "Green"
$script:ErrorColor = "Red"
$script:WarningColor = "Yellow"
$script:InfoColor = "Cyan"

# 크롤러 목록
$crawlers = @(
    @{ Name = "ppomppu"; TaskDef = "ppomppu-crawler-task" },
    @{ Name = "ruliweb"; TaskDef = "ruliweb-crawler-task" },
    @{ Name = "fmkorea"; TaskDef = "fmkorea-crawler-task" },
    @{ Name = "quasarzone"; TaskDef = "quasarzone-crawler-task" },
    @{ Name = "arcalive"; TaskDef = "arcalive-crawler-task" },
    @{ Name = "eomisae"; TaskDef = "eomisae-crawler-task" }
)

# 결과 저장
$results = @()
$taskArns = @{}

#==============================================================================
# 함수 정의
#==============================================================================

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    
    if ($NoNewline) {
        Write-Host $Message -ForegroundColor $Color -NoNewline
    } else {
        Write-Host $Message -ForegroundColor $Color
    }
}

function Write-Header {
    param([string]$Title)
    
    Write-Host ""
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -Color $InfoColor
    Write-ColorOutput "  $Title" -Color $InfoColor
    Write-ColorOutput "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -Color $InfoColor
    Write-Host ""
}

function Test-AWSCli {
    try {
        $null = aws --version 2>&1
        return $true
    } catch {
        return $false
    }
}

function Get-SubnetAndSG {
    Write-ColorOutput "[INFO] VPC 정보 조회 중..." -Color $InfoColor
    
    # 기본 VPC 찾기
    $defaultVpc = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region $Region --query "Vpcs[0].VpcId" --output text 2>$null
    
    if ($defaultVpc -and $defaultVpc -ne "None") {
        Write-ColorOutput "[OK] 기본 VPC 발견: $defaultVpc" -Color $SuccessColor
        
        # Subnet 찾기
        if (-not $script:SubnetId) {
            $subnet = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$defaultVpc" --region $Region --query "Subnets[0].SubnetId" --output text 2>$null
            if ($subnet -and $subnet -ne "None") {
                $script:SubnetId = $subnet
                Write-ColorOutput "[OK] Subnet 발견: $subnet" -Color $SuccessColor
            }
        }
        
        # Security Group 찾기
        if (-not $script:SecurityGroupId) {
            $sg = aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$defaultVpc" "Name=group-name,Values=default" --region $Region --query "SecurityGroups[0].GroupId" --output text 2>$null
            if ($sg -and $sg -ne "None") {
                $script:SecurityGroupId = $sg
                Write-ColorOutput "[OK] Security Group 발견: $sg" -Color $SuccessColor
            }
        }
    }
    
    # 수동 입력 필요 여부 확인
    if (-not $script:SubnetId -or -not $script:SecurityGroupId) {
        Write-ColorOutput "[ERROR] VPC 설정을 찾을 수 없습니다." -Color $ErrorColor
        Write-ColorOutput "다음 명령어로 직접 확인 후 스크립트에 전달하세요:" -Color $WarningColor
        Write-Host ""
        Write-Host "  # Subnet 확인"
        Write-Host "  aws ec2 describe-subnets --region $Region --query 'Subnets[0].SubnetId' --output text"
        Write-Host ""
        Write-Host "  # Security Group 확인"
        Write-Host "  aws ec2 describe-security-groups --region $Region --query 'SecurityGroups[0].GroupId' --output text"
        Write-Host ""
        Write-Host "  # 스크립트 실행 예시"
        Write-Host "  .\Test-FargateCrawlers.ps1 -SubnetId subnet-xxxx -SecurityGroupId sg-xxxx"
        Write-Host ""
        return $false
    }
    
    return $true
}

function Start-CrawlerTask {
    param(
        [string]$TaskDefinition,
        [string]$CrawlerName
    )
    
    Write-ColorOutput "[RUN] $CrawlerName Task 시작 중..." -Color $InfoColor
    
    $networkConfig = @"
{
    "awsvpcConfiguration": {
        "subnets": ["$SubnetId"],
        "securityGroups": ["$SecurityGroupId"],
        "assignPublicIp": "ENABLED"
    }
}
"@
    
    try {
        $output = aws ecs run-task `
            --cluster $ClusterName `
            --task-definition $TaskDefinition `
            --launch-type FARGATE `
            --network-configuration $networkConfig `
            --region $Region `
            2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $taskArn = ($output | ConvertFrom-Json).tasks[0].taskArn
            Write-ColorOutput "[OK] Task 시작 성공: $taskArn" -Color $SuccessColor
            return $taskArn
        } else {
            Write-ColorOutput "[ERROR] Task 시작 실패" -Color $ErrorColor
            Write-ColorOutput $output -Color $ErrorColor
            return $null
        }
    } catch {
        Write-ColorOutput "[ERROR] $($_.Exception.Message)" -Color $ErrorColor
        return $null
    }
}

function Wait-TaskCompletion {
    param(
        [hashtable]$TaskArns,
        [int]$TimeoutMinutes
    )
    
    Write-Header "Task 완료 대기 중 (최대 $TimeoutMinutes 분)"
    
    $startTime = Get-Date
    $timeout = $startTime.AddMinutes($TimeoutMinutes)
    $checkInterval = 10  # 10초마다 확인
    
    $completedTasks = @{}
    
    while ((Get-Date) -lt $timeout) {
        $allCompleted = $true
        
        foreach ($crawler in $TaskArns.Keys) {
            if ($completedTasks.ContainsKey($crawler)) {
                continue
            }
            
            $taskArn = $TaskArns[$crawler]
            if (-not $taskArn) {
                $completedTasks[$crawler] = "FAILED_TO_START"
                continue
            }
            
            try {
                $taskStatus = aws ecs describe-tasks `
                    --cluster $ClusterName `
                    --tasks $taskArn `
                    --region $Region `
                    --query "tasks[0].lastStatus" `
                    --output text `
                    2>$null
                
                if ($taskStatus -eq "STOPPED") {
                    $exitCode = aws ecs describe-tasks `
                        --cluster $ClusterName `
                        --tasks $taskArn `
                        --region $Region `
                        --query "tasks[0].containers[0].exitCode" `
                        --output text `
                        2>$null
                    
                    $completedTasks[$crawler] = if ($exitCode -eq "0") { "SUCCESS" } else { "FAILED" }
                    Write-ColorOutput "[완료] $crawler - 상태: $($completedTasks[$crawler])" -Color $(if ($exitCode -eq "0") { $SuccessColor } else { $ErrorColor })
                } else {
                    $allCompleted = $false
                    Write-ColorOutput "[대기] $crawler - 상태: $taskStatus" -Color $WarningColor
                }
            } catch {
                Write-ColorOutput "[ERROR] $crawler 상태 확인 실패: $($_.Exception.Message)" -Color $ErrorColor
                $completedTasks[$crawler] = "ERROR"
            }
        }
        
        if ($allCompleted) {
            Write-ColorOutput "`n[OK] 모든 Task 완료!" -Color $SuccessColor
            break
        }
        
        Write-ColorOutput "다음 확인까지 $checkInterval 초 대기..." -Color $InfoColor
        Start-Sleep -Seconds $checkInterval
    }
    
    if (-not $allCompleted) {
        Write-ColorOutput "`n[WARNING] 타임아웃: 일부 Task가 아직 실행 중입니다." -Color $WarningColor
        
        foreach ($crawler in $TaskArns.Keys) {
            if (-not $completedTasks.ContainsKey($crawler)) {
                $completedTasks[$crawler] = "TIMEOUT"
            }
        }
    }
    
    return $completedTasks
}

function Get-CrawlerLogs {
    param(
        [string]$TaskArn,
        [string]$CrawlerName
    )
    
    Write-ColorOutput "`n[로그] $CrawlerName 로그 수집 중..." -Color $InfoColor
    
    # Task ID 추출
    $taskId = ($TaskArn -split "/")[-1]
    $logGroup = "/ecs/$CrawlerName-crawler"
    
    try {
        # 로그 스트림 찾기
        $logStreams = aws logs describe-log-streams `
            --log-group-name $logGroup `
            --region $Region `
            --order-by LastEventTime `
            --descending `
            --max-items 5 `
            --query "logStreams[*].logStreamName" `
            --output json `
            2>$null | ConvertFrom-Json
        
        if (-not $logStreams) {
            Write-ColorOutput "[WARNING] 로그 스트림을 찾을 수 없습니다." -Color $WarningColor
            return $null
        }
        
        # Task ID가 포함된 스트림 찾기
        $matchingStream = $logStreams | Where-Object { $_ -match $taskId } | Select-Object -First 1
        
        if (-not $matchingStream) {
            # Task ID가 없으면 최신 스트림 사용
            $matchingStream = $logStreams[0]
        }
        
        Write-ColorOutput "[INFO] 로그 스트림: $matchingStream" -Color $InfoColor
        
        # 로그 가져오기
        $logs = aws logs get-log-events `
            --log-group-name $logGroup `
            --log-stream-name $matchingStream `
            --region $Region `
            --output json `
            2>$null | ConvertFrom-Json
        
        if ($logs.events) {
            Write-ColorOutput "[OK] 로그 수집 완료 ($($logs.events.Count) 줄)" -Color $SuccessColor
            
            # 로그 파일로 저장
            $logFile = "logs\$CrawlerName-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
            New-Item -ItemType Directory -Force -Path "logs" | Out-Null
            
            $logs.events | ForEach-Object {
                $timestamp = [DateTimeOffset]::FromUnixTimeMilliseconds($_.timestamp).ToString("yyyy-MM-dd HH:mm:ss")
                "$timestamp | $($_.message)" | Out-File -Append -FilePath $logFile -Encoding UTF8
            }
            
            Write-ColorOutput "[저장] $logFile" -Color $SuccessColor
            
            # 중요 정보 추출
            $importantLines = $logs.events | Where-Object { 
                $_.message -match "총.*개 수집|크롤링 완료|ERROR|FAIL"
            } | Select-Object -Last 10
            
            if ($importantLines) {
                Write-ColorOutput "`n[주요 로그]" -Color $InfoColor
                foreach ($line in $importantLines) {
                    $msg = $line.message.Trim()
                    if ($msg -match "ERROR|FAIL") {
                        Write-ColorOutput "  $msg" -Color $ErrorColor
                    } else {
                        Write-ColorOutput "  $msg" -Color $SuccessColor
                    }
                }
            }
            
            return $logFile
        } else {
            Write-ColorOutput "[WARNING] 로그가 비어있습니다." -Color $WarningColor
            return $null
        }
        
    } catch {
        Write-ColorOutput "[ERROR] 로그 수집 실패: $($_.Exception.Message)" -Color $ErrorColor
        return $null
    }
}

function Show-Summary {
    param(
        [hashtable]$CompletedTasks,
        [array]$Results
    )
    
    Write-Header "테스트 결과 요약"
    
    $successCount = ($CompletedTasks.Values | Where-Object { $_ -eq "SUCCESS" }).Count
    $failCount = ($CompletedTasks.Values | Where-Object { $_ -ne "SUCCESS" }).Count
    
    Write-Host ""
    Write-ColorOutput "전체 크롤러: $($CompletedTasks.Count)개" -Color $InfoColor
    Write-ColorOutput "성공: $successCount 개" -Color $SuccessColor
    Write-ColorOutput "실패: $failCount 개" -Color $ErrorColor
    Write-Host ""
    
    Write-Host "크롤러별 결과:"
    Write-Host "─────────────────────────────────────"
    
    foreach ($result in $Results) {
        $status = $result.Status
        $color = switch ($status) {
            "SUCCESS" { $SuccessColor }
            "FAILED" { $ErrorColor }
            "TIMEOUT" { $WarningColor }
            "FAILED_TO_START" { $ErrorColor }
            default { "White" }
        }
        
        $statusText = switch ($status) {
            "SUCCESS" { "✓ 성공" }
            "FAILED" { "✗ 실패" }
            "TIMEOUT" { "⏱ 타임아웃" }
            "FAILED_TO_START" { "✗ 시작 실패" }
            default { "? 알 수 없음" }
        }
        
        Write-ColorOutput "  $($result.Crawler.PadRight(15)) : $statusText" -Color $color
        
        if ($result.LogFile) {
            Write-ColorOutput "    로그: $($result.LogFile)" -Color "Gray"
        }
    }
    
    Write-Host ""
    Write-Host "─────────────────────────────────────"
    Write-Host ""
    
    if ($failCount -eq 0) {
        Write-ColorOutput "[완료] 모든 크롤러 테스트 성공! 🎉" -Color $SuccessColor
    } else {
        Write-ColorOutput "[경고] 일부 크롤러 테스트 실패" -Color $WarningColor
    }
}

#==============================================================================
# 메인 실행
#==============================================================================

try {
    Write-Header "Fargate 크롤러 전체 테스트"
    
    Write-Host "설정:"
    Write-Host "  리전: $Region"
    Write-Host "  클러스터: $ClusterName"
    Write-Host "  대기 시간: $WaitMinutes 분"
    Write-Host ""
    
    # 1. AWS CLI 확인
    Write-ColorOutput "[1/5] AWS CLI 확인 중..." -Color $InfoColor
    if (-not (Test-AWSCli)) {
        Write-ColorOutput "[ERROR] AWS CLI가 설치되어 있지 않습니다." -Color $ErrorColor
        Write-ColorOutput "설치: https://aws.amazon.com/cli/" -Color $WarningColor
        exit 1
    }
    Write-ColorOutput "[OK] AWS CLI 확인 완료" -Color $SuccessColor
    
    # 2. VPC 설정 확인
    Write-ColorOutput "`n[2/5] VPC 설정 확인 중..." -Color $InfoColor
    if (-not (Get-SubnetAndSG)) {
        exit 1
    }
    
    # 3. Task 시작
    Write-Header "[3/5] 크롤러 Task 시작"
    
    foreach ($crawler in $crawlers) {
        $taskArn = Start-CrawlerTask -TaskDefinition $crawler.TaskDef -CrawlerName $crawler.Name
        if ($taskArn) {
            $taskArns[$crawler.Name] = $taskArn
        }
        Start-Sleep -Seconds 2  # API Rate Limit 방지
    }
    
    if ($taskArns.Count -eq 0) {
        Write-ColorOutput "`n[ERROR] 시작된 Task가 없습니다." -Color $ErrorColor
        exit 1
    }
    
    # 4. Task 완료 대기
    $completedTasks = Wait-TaskCompletion -TaskArns $taskArns -TimeoutMinutes $WaitMinutes
    
    # 5. 로그 수집
    Write-Header "[4/5] 로그 수집"
    
    foreach ($crawler in $crawlers) {
        if ($taskArns.ContainsKey($crawler.Name) -and $taskArns[$crawler.Name]) {
            $logFile = Get-CrawlerLogs -TaskArn $taskArns[$crawler.Name] -CrawlerName $crawler.Name
            
            $results += @{
                Crawler = $crawler.Name
                Status = $completedTasks[$crawler.Name]
                TaskArn = $taskArns[$crawler.Name]
                LogFile = $logFile
            }
        } else {
            $results += @{
                Crawler = $crawler.Name
                Status = "FAILED_TO_START"
                TaskArn = $null
                LogFile = $null
            }
        }
    }
    
    # 6. 결과 요약
    Show-Summary -CompletedTasks $completedTasks -Results $results
    
    # 종료 코드 설정
    $failCount = ($completedTasks.Values | Where-Object { $_ -ne "SUCCESS" }).Count
    if ($failCount -gt 0) {
        exit 1
    } else {
        exit 0
    }
    
} catch {
    Write-ColorOutput "`n[ERROR] 예상치 못한 오류 발생" -Color $ErrorColor
    Write-ColorOutput $_.Exception.Message -Color $ErrorColor
    Write-ColorOutput $_.ScriptStackTrace -Color "Gray"
    exit 1
}
