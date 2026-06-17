$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "    PIZZA CLUB - BUILD LAUNCHER EXE + PACKAGE DEPLOYMENT" -ForegroundColor Cyan
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Compile tiny C# launcher EXE
Write-Host "  [1/3] Compiling PizzaClub.exe launcher..." -ForegroundColor Yellow

$CsFile = "$ProjectRoot\PizzaClub_Launcher.cs"
if (-not (Test-Path $CsFile)) {
    Write-Host "  [ERROR] PizzaClub_Launcher.cs not found." -ForegroundColor Red
    exit 1
}

$CSharpCode = Get-Content $CsFile -Raw

$CompilerParams = New-Object System.CodeDom.Compiler.CompilerParameters
$CompilerParams.GenerateExecutable = $true
$CompilerParams.OutputAssembly = "$ProjectRoot\PizzaClub.exe"
$CompilerParams.ReferencedAssemblies.Add("System.Windows.Forms.dll") | Out-Null
$CompilerParams.ReferencedAssemblies.Add("System.dll") | Out-Null
$CompilerParams.CompilerOptions = "/target:winexe /optimize+"

$IconPath = "$ProjectRoot\static\pizza_club_logo.ico"
if (Test-Path $IconPath) {
    $CompilerParams.CompilerOptions += " /win32icon:`"$IconPath`""
    Write-Host "  [INFO] Embedding icon: pizza_club_logo.ico" -ForegroundColor DarkGray
}

$Provider = New-Object Microsoft.CSharp.CSharpCodeProvider
$Result = $Provider.CompileAssemblyFromSource($CompilerParams, $CSharpCode)

if ($Result.Errors.Count -gt 0) {
    Write-Host "  [ERROR] Compilation failed:" -ForegroundColor Red
    $Result.Errors | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    exit 1
}

$exeSize = [math]::Round((Get-Item "$ProjectRoot\PizzaClub.exe").Length / 1KB, 1)
Write-Host "  [OK]   PizzaClub.exe compiled ($exeSize KB) - tiny launcher, not standalone." -ForegroundColor Green

# Step 2: Gather deployment files
Write-Host ""
Write-Host "  [2/3] Assembling deployment package..." -ForegroundColor Yellow

$Date = Get-Date -Format "yyyy-MM-dd_HHmmss"
$OutName = "PizzaClub_Deploy_$Date"
$StagingDir = "$ProjectRoot\$OutName"
$ZipPath = "$ProjectRoot\$OutName.zip"

if (Test-Path $StagingDir) { Remove-Item $StagingDir -Recurse -Force }
New-Item -ItemType Directory -Path $StagingDir | Out-Null

$FilesToCopy = @(
    "main.py",
    "PizzaClub.exe",
    "requirements.txt",
    "config.json",
    "yolov8n.pt",
    "WATCHDOG.bat",
    "START_HIDDEN.vbs",
    "INSTALL_SERVICE.bat",
    "STOP_SERVICE.bat",
    "STATUS.bat",
    "UNINSTALL_SERVICE.bat",
    "CHANGE_PORT_AND_LAUNCH.bat",
    "START_REMOTE_ACCESS.bat",
    "SETUP_VENV.bat",
    "OPERATIONS_GUIDE.html",
    "SERVER_SETUP_GUIDE.html",
    "README_PIZZA_CLUB.html"
)

foreach ($f in $FilesToCopy) {
    $src = "$ProjectRoot\$f"
    if (Test-Path $src) {
        Copy-Item $src "$StagingDir\$f" -Force
        Write-Host "    + $f" -ForegroundColor DarkGray
    }
    else {
        Write-Host "    ! $f (not found - skipped)" -ForegroundColor DarkYellow
    }
}

foreach ($folder in @("templates", "static")) {
    $src = "$ProjectRoot\$folder"
    if (Test-Path $src) {
        Copy-Item $src "$StagingDir\$folder" -Recurse -Force
        Write-Host "    + $folder\" -ForegroundColor DarkGray
    }
}

# Step 3: Compress to ZIP
Write-Host ""
Write-Host "  [3/3] Compressing to ZIP..." -ForegroundColor Yellow

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path "$StagingDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal
Remove-Item $StagingDir -Recurse -Force

$ZipSize = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host "    PACKAGE READY" -ForegroundColor Green
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "    Output : $ZipPath" -ForegroundColor White
Write-Host "    Size   : $ZipSize MB" -ForegroundColor White
Write-Host ""
Write-Host "  Deployment Instructions for the target machine:" -ForegroundColor Cyan
Write-Host "    1. Extract the ZIP anywhere (e.g. C:\PizzaClub\)" -ForegroundColor White
Write-Host "    2. Install Python 3.11 from python.org if not already installed" -ForegroundColor White
Write-Host "    3. Run SETUP_VENV.bat once to install Python packages" -ForegroundColor White
Write-Host "    4. Edit config.json with your camera IP and branch name" -ForegroundColor White
Write-Host "    5. Run INSTALL_SERVICE.bat as Administrator" -ForegroundColor White
Write-Host "       (registers autostart + launches server immediately)" -ForegroundColor White
Write-Host "    6. Or just double-click PizzaClub.exe to start now" -ForegroundColor White
Write-Host ""
Write-Host "  NOTE: The EXE is a tiny launcher (~30KB), NOT a standalone bundle." -ForegroundColor DarkYellow
Write-Host "        Server runs via venv Python in the background." -ForegroundColor DarkYellow
Write-Host "        Target machine MUST have Python 3.11 installed." -ForegroundColor DarkYellow
Write-Host ""
