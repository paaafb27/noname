# create_layer.ps1
# Lambda Layer Creation Script for Windows PowerShell
# Encoding: UTF-8

param(
    [switch]$SkipInstall = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Lambda Layer Creation Started" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Path Settings
$PROJECT_ROOT = "F:\scandeals-crawler"
$LAYER_DIR = "$PROJECT_ROOT\layers\playwright"
$PYTHON_DIR = "$LAYER_DIR\python"
$DEPLOY_DIR = "$PROJECT_ROOT\deploy"
$ZIP_FILE = "$DEPLOY_DIR\playwright-layer.zip"

# 1. Check Python Directory
if (-Not (Test-Path $PYTHON_DIR)) {
    Write-Host "[ERROR] python directory not found: $PYTHON_DIR" -ForegroundColor Red
    Write-Host "Please install packages first:" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt -t python/" -ForegroundColor Yellow
    exit 1
}

# 2. Package Installation (Optional)
if (-Not $SkipInstall) {
    Write-Host "[1/6] Reinstalling packages... (This may take a while)" -ForegroundColor Yellow

    # Remove existing packages
    if (Test-Path $PYTHON_DIR) {
        Write-Host "  Removing existing packages..." -ForegroundColor Gray
        Get-ChildItem -Path $PYTHON_DIR -Exclude ".gitkeep" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Install packages
    Set-Location $LAYER_DIR

    Write-Host "  Installing playwright..." -ForegroundColor Gray
    pip install playwright==1.40.0 -t python/ --no-cache-dir --quiet

    Write-Host "  Installing beautifulsoup4..." -ForegroundColor Gray
    pip install beautifulsoup4==4.12.2 -t python/ --no-cache-dir --quiet

    Write-Host "  Installing lxml..." -ForegroundColor Gray
    pip install lxml==4.9.3 -t python/ --no-cache-dir --quiet

    Write-Host "  Installing requests..." -ForegroundColor Gray
    pip install requests==2.31.0 -t python/ --no-cache-dir --quiet

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Package installation failed" -ForegroundColor Red
        exit 1
    }

    Write-Host "  Package installation completed" -ForegroundColor Green
}
else {
    Write-Host "[1/6] Package installation skipped (-SkipInstall option)" -ForegroundColor Yellow
}

# 3. Install Playwright Browsers
Write-Host "[2/6] Installing Playwright browsers..." -ForegroundColor Yellow
Set-Location $PYTHON_DIR

# Check if playwright module exists
$playwrightPath = Join-Path $PYTHON_DIR "playwright"
if (Test-Path $playwrightPath) {
    & python -m playwright install chromium --with-deps 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Playwright browsers installed" -ForegroundColor Green
    }
    else {
        Write-Host "  [WARNING] Playwright browser installation failed (OK for Lambda)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "  [WARNING] Playwright module not found. Skipping browser installation." -ForegroundColor Yellow
}

# 4. Remove Unnecessary Files
Write-Host "[3/6] Removing unnecessary files..." -ForegroundColor Yellow

$removePatterns = @(
    "*.pyc",
    "*.pyo",
    "__pycache__",
    "*.dist-info",
    "*.egg-info",
    "tests",
    "test"
)

foreach ($pattern in $removePatterns) {
    Get-ChildItem -Path $PYTHON_DIR -Recurse -Filter $pattern -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "  Cleanup completed" -ForegroundColor Green

# 5. Check Directory Size
Write-Host "[4/6] Checking directory size..." -ForegroundColor Yellow
$sizeInMB = (Get-ChildItem -Path $PYTHON_DIR -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
$roundedSize = [math]::Round($sizeInMB, 2)
Write-Host "  python/ size: $roundedSize MB" -ForegroundColor Cyan

if ($sizeInMB -lt 50) {
    Write-Host "" -ForegroundColor White
    Write-Host "[WARNING] Directory size is too small ($roundedSize MB)" -ForegroundColor Yellow
    Write-Host "Playwright may not be installed correctly." -ForegroundColor Yellow
    Write-Host "" -ForegroundColor White

    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne 'y') {
        Write-Host "Aborted. Please reinstall packages:" -ForegroundColor Red
        Write-Host "  Remove-Item -Path '$PYTHON_DIR' -Recurse -Force" -ForegroundColor Yellow
        Write-Host "  pip install playwright==1.40.0 beautifulsoup4==4.12.2 lxml==4.9.3 requests==2.31.0 -t python/" -ForegroundColor Yellow
        exit 1
    }
}

# 6. Remove Existing ZIP File
if (Test-Path $ZIP_FILE) {
    Write-Host "[5/6] Removing existing ZIP file..." -ForegroundColor Yellow
    Remove-Item $ZIP_FILE -Force
}

# 7. Create ZIP File
Write-Host "[6/6] Creating ZIP file... (This may take 3-5 minutes)" -ForegroundColor Yellow

try {
    Set-Location $LAYER_DIR
    Compress-Archive -Path "python" -DestinationPath $ZIP_FILE -CompressionLevel Optimal -Force
    Write-Host "  ZIP file created successfully" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] ZIP file creation failed: $_" -ForegroundColor Red
    exit 1
}

# 8. Verify Created ZIP File
Write-Host "" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path $ZIP_FILE) {
    $zipSizeInMB = (Get-Item $ZIP_FILE).Length / 1MB
    $roundedZipSize = [math]::Round($zipSizeInMB, 2)

    Write-Host "SUCCESS: Layer created!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "File location: $ZIP_FILE" -ForegroundColor White
    Write-Host "File size: $roundedZipSize MB" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan

    # Size Validation
    if ($zipSizeInMB -lt 50) {
        Write-Host "" -ForegroundColor White
        Write-Host "[WARNING] ZIP file is too small (under 50MB)" -ForegroundColor Yellow
        Write-Host "Playwright may be missing." -ForegroundColor Yellow
        Write-Host "" -ForegroundColor White
        Write-Host "SOLUTION: Reinstall packages" -ForegroundColor Cyan
        Write-Host "  cd F:\scandeals-crawler\layers\playwright" -ForegroundColor Gray
        Write-Host "  Remove-Item -Path python -Recurse -Force" -ForegroundColor Gray
        Write-Host "  pip install playwright==1.40.0 beautifulsoup4==4.12.2 lxml==4.9.3 requests==2.31.0 -t python/" -ForegroundColor Gray
        Write-Host "  cd F:\scandeals-crawler\deploy" -ForegroundColor Gray
        Write-Host "  PowerShell -ExecutionPolicy Bypass -File .\create_layer.ps1 -SkipInstall" -ForegroundColor Gray
    }
    elseif ($zipSizeInMB -gt 250) {
        Write-Host "" -ForegroundColor White
        Write-Host "[WARNING] ZIP file is large (over 250MB)" -ForegroundColor Yellow
        Write-Host "Cannot upload directly to Lambda." -ForegroundColor Yellow
        Write-Host "Must use S3." -ForegroundColor Yellow
    }
    else {
        Write-Host "" -ForegroundColor White
        Write-Host "SUCCESS: Normal size (50-250MB)" -ForegroundColor Green
    }
}
else {
    Write-Host "ERROR: ZIP file was not created" -ForegroundColor Red
    exit 1
}

# 9. Next Steps
Write-Host "" -ForegroundColor White
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if ($zipSizeInMB -gt 50) {
    Write-Host "WARNING: ZIP file exceeds 50MB" -ForegroundColor Yellow
    Write-Host "S3 upload required:" -ForegroundColor Yellow
    Write-Host "" -ForegroundColor White
    Write-Host "1. Create S3 bucket (AWS Console)" -ForegroundColor White
    Write-Host "2. Upload ZIP file:" -ForegroundColor White
    Write-Host "   aws s3 cp $ZIP_FILE s3://YOUR-BUCKET-NAME/" -ForegroundColor Gray
    Write-Host "3. Create Lambda Layer (specify S3 path)" -ForegroundColor White
}
else {
    Write-Host "SUCCESS: Direct upload possible" -ForegroundColor Green
    Write-Host "" -ForegroundColor White
    Write-Host "1. Go to AWS Lambda Console" -ForegroundColor White
    Write-Host "2. Layers -> Create layer" -ForegroundColor White
    Write-Host "3. Upload: $ZIP_FILE" -ForegroundColor White
    Write-Host "4. Runtime: Select Python 3.11" -ForegroundColor White
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White