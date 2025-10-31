# Subnet과 Security Group 자동 조회 스크립트
# 목적: EventBridge 설정에 필요한 네트워크 정보 자동 조회

$REGION = "ap-northeast-2"

Write-Host "================================" -ForegroundColor Magenta
Write-Host "네트워크 정보 자동 조회" -ForegroundColor Magenta
Write-Host "================================`n" -ForegroundColor Magenta

# 1. VPC 조회
Write-Host "[1] VPC 조회" -ForegroundColor Yellow
$vpcs = aws ec2 describe-vpcs --region $REGION | ConvertFrom-Json

if ($vpcs.Vpcs.Count -gt 0) {
    Write-Host "`n사용 가능한 VPC:" -ForegroundColor Cyan
    foreach ($vpc in $vpcs.Vpcs) {
        $vpcName = ($vpc.Tags | Where-Object { $_.Key -eq "Name" }).Value
        $isDefault = if ($vpc.IsDefault) { " (기본 VPC)" } else { "" }
        Write-Host "  VPC ID: $($vpc.VpcId) - $vpcName$isDefault" -ForegroundColor White
        Write-Host "  CIDR: $($vpc.CidrBlock)" -ForegroundColor Gray
    }

    # 기본 VPC 선택
    $defaultVpc = $vpcs.Vpcs | Where-Object { $_.IsDefault -eq $true } | Select-Object -First 1
    if ($defaultVpc) {
        $selectedVpcId = $defaultVpc.VpcId
        Write-Host "`n✅ 선택된 VPC: $selectedVpcId (기본 VPC)" -ForegroundColor Green
    } else {
        $selectedVpcId = $vpcs.Vpcs[0].VpcId
        Write-Host "`n✅ 선택된 VPC: $selectedVpcId" -ForegroundColor Green
    }
} else {
    Write-Host "❌ VPC가 없습니다" -ForegroundColor Red
    exit 1
}

# 2. Public Subnet 조회
Write-Host "`n[2] Public Subnet 조회 (선택된 VPC 내)" -ForegroundColor Yellow
$subnets = aws ec2 describe-subnets `
    --region $REGION `
    --filters "Name=vpc-id,Values=$selectedVpcId" "Name=map-public-ip-on-launch,Values=true" `
    | ConvertFrom-Json

if ($subnets.Subnets.Count -gt 0) {
    Write-Host "`n사용 가능한 Public Subnet:" -ForegroundColor Cyan
    foreach ($subnet in $subnets.Subnets) {
        $subnetName = ($subnet.Tags | Where-Object { $_.Key -eq "Name" }).Value
        Write-Host "  Subnet ID: $($subnet.SubnetId)" -ForegroundColor White
        Write-Host "  AZ: $($subnet.AvailabilityZone)" -ForegroundColor Gray
        Write-Host "  CIDR: $($subnet.CidrBlock)" -ForegroundColor Gray
        if ($subnetName) {
            Write-Host "  Name: $subnetName" -ForegroundColor Gray
        }
        Write-Host ""
    }

    $selectedSubnetId = $subnets.Subnets[0].SubnetId
    Write-Host "✅ 선택된 Subnet: $selectedSubnetId" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Public Subnet이 없습니다. 일반 Subnet 조회..." -ForegroundColor Yellow

    $subnets = aws ec2 describe-subnets `
        --region $REGION `
        --filters "Name=vpc-id,Values=$selectedVpcId" `
        | ConvertFrom-Json

    if ($subnets.Subnets.Count -gt 0) {
        $selectedSubnetId = $subnets.Subnets[0].SubnetId
        Write-Host "✅ 선택된 Subnet: $selectedSubnetId (Public IP 자동 할당 비활성화)" -ForegroundColor Yellow
        Write-Host "   ⚠️  ECS Task에서 AssignPublicIp=ENABLED 설정 필요" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Subnet이 없습니다" -ForegroundColor Red
        exit 1
    }
}

# 3. Security Group 조회
Write-Host "`n[3] Security Group 조회" -ForegroundColor Yellow
$securityGroups = aws ec2 describe-security-groups `
    --region $REGION `
    --filters "Name=vpc-id,Values=$selectedVpcId" `
    | ConvertFrom-Json

if ($securityGroups.SecurityGroups.Count -gt 0) {
    Write-Host "`n사용 가능한 Security Group:" -ForegroundColor Cyan

    # 기본 Security Group 찾기
    $defaultSg = $securityGroups.SecurityGroups | Where-Object { $_.GroupName -eq "default" } | Select-Object -First 1

    foreach ($sg in $securityGroups.SecurityGroups) {
        $isDefault = if ($sg.GroupId -eq $defaultSg.GroupId) { " (기본)" } else { "" }
        Write-Host "  SG ID: $($sg.GroupId)$isDefault" -ForegroundColor White
        Write-Host "  Name: $($sg.GroupName)" -ForegroundColor Gray
        Write-Host "  Description: $($sg.Description)" -ForegroundColor Gray

        # Outbound 규칙 확인
        $hasHttpsOutbound = $sg.IpPermissionsEgress | Where-Object {
            $_.IpProtocol -eq "-1" -or ($_.IpProtocol -eq "tcp" -and $_.ToPort -eq 443)
        }

        if ($hasHttpsOutbound) {
            Write-Host "  Outbound: ✅ HTTPS(443) 허용됨" -ForegroundColor Green
        } else {
            Write-Host "  Outbound: ⚠️  HTTPS(443) 규칙 확인 필요" -ForegroundColor Yellow
        }
        Write-Host ""
    }

    # 기본 SG 선택 또는 첫 번째 SG
    if ($defaultSg) {
        $selectedSgId = $defaultSg.GroupId
        Write-Host "✅ 선택된 Security Group: $selectedSgId (기본)" -ForegroundColor Green
    } else {
        $selectedSgId = $securityGroups.SecurityGroups[0].GroupId
        Write-Host "✅ 선택된 Security Group: $selectedSgId" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Security Group이 없습니다" -ForegroundColor Red
    exit 1
}

# 4. Security Group의 Outbound 규칙 상세 확인
Write-Host "`n[4] 선택된 Security Group의 Outbound 규칙 확인" -ForegroundColor Yellow
$selectedSg = $securityGroups.SecurityGroups | Where-Object { $_.GroupId -eq $selectedSgId }

Write-Host "Egress Rules:" -ForegroundColor Cyan
foreach ($rule in $selectedSg.IpPermissionsEgress) {
    if ($rule.IpProtocol -eq "-1") {
        Write-Host "  ✅ 모든 트래픽 허용 (0.0.0.0/0)" -ForegroundColor Green
    } else {
        $fromPort = if ($rule.FromPort) { $rule.FromPort } else { "N/A" }
        $toPort = if ($rule.ToPort) { $rule.ToPort } else { "N/A" }
        Write-Host "  Protocol: $($rule.IpProtocol), Ports: $fromPort-$toPort" -ForegroundColor White
    }
}

$hasFullOutbound = $selectedSg.IpPermissionsEgress | Where-Object { $_.IpProtocol -eq "-1" }
if (-not $hasFullOutbound) {
    Write-Host "`n⚠️  경고: HTTPS(443) Outbound 규칙이 명시적으로 필요할 수 있습니다" -ForegroundColor Yellow
    Write-Host "다음 명령으로 추가:" -ForegroundColor White
    Write-Host "aws ec2 authorize-security-group-egress --group-id $selectedSgId --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $REGION" -ForegroundColor Cyan
}

# 5. 최종 설정값 출력
Write-Host "`n================================" -ForegroundColor Magenta
Write-Host "✅ 네트워크 설정값 (복사하여 사용)" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Magenta

Write-Host "`n# create-eventbridge-rules.ps1 에 입력할 값:`n" -ForegroundColor Yellow
Write-Host "`$SUBNET_ID = `"$selectedSubnetId`"" -ForegroundColor Cyan
Write-Host "`$SG_ID = `"$selectedSgId`"" -ForegroundColor Cyan

Write-Host "`n또는 PowerShell 변수로 직접 사용:" -ForegroundColor Yellow
Write-Host "`$env:SUBNET_ID = `"$selectedSubnetId`"" -ForegroundColor Cyan
Write-Host "`$env:SG_ID = `"$selectedSgId`"`n" -ForegroundColor Cyan

# 6. 자동으로 환경 변수 설정
$env:SUBNET_ID = $selectedSubnetId
$env:SG_ID = $selectedSgId

Write-Host "✅ 환경 변수 설정 완료 (현재 세션에서 유효)" -ForegroundColor Green
Write-Host "   `$env:SUBNET_ID = $env:SUBNET_ID" -ForegroundColor Gray
Write-Host "   `$env:SG_ID = $env:SG_ID`n" -ForegroundColor Gray

# 7. 다음 단계 안내
Write-Host "================================" -ForegroundColor Magenta
Write-Host "다음 단계" -ForegroundColor Magenta
Write-Host "================================" -ForegroundColor Magenta

Write-Host "`n1. create-eventbridge-rules.ps1 파일 수정:" -ForegroundColor White
Write-Host "   위의 SUBNET_ID와 SG_ID 값을 복사하여 입력" -ForegroundColor Gray

Write-Host "`n2. EventBridge 스케줄 생성:" -ForegroundColor White
Write-Host "   .\create-eventbridge-rules.ps1" -ForegroundColor Cyan

Write-Host "`n3. 수동 테스트 (선택사항):" -ForegroundColor White
Write-Host "   .\run-task-manual-test.ps1 (파일 내 SUBNET_ID, SG_ID도 동일하게 수정)" -ForegroundColor Cyan

Write-Host ""