$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "    PIZZA CLUB - BUILD STANDALONE OFFLINE PACKAGE" -ForegroundColor Cyan
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  This will package an embedded Python environment, meaning" -ForegroundColor Yellow
Write-Host "  the target machine will NOT need Python installed at all." -ForegroundColor Yellow
Write-Host ""

# Step 1: Compile tiny C# launcher EXE
Write-Host "  [1/4] Compiling PizzaClub.exe launcher..." -ForegroundColor Yellow
$CsFile = "$ProjectRoot\PizzaClub_Launcher.cs"

# We must dynamically update the C# launcher to point to system\python.exe instead 
# of venv_311, and to not nag about SETUP_VENV.bat. So we generate it on the fly.
$CSharpCode = @"
using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

class PizzaClub {
    [STAThread]
    static void Main(string[] args) {
        string exeDir  = AppDomain.CurrentDomain.BaseDirectory;
        string vbsPath = Path.Combine(exeDir, "START_HIDDEN.vbs");

        if (!File.Exists(vbsPath)) {
            MessageBox.Show(
                "START_HIDDEN.vbs not found in:\n" + exeDir,
                "PizzaClub - Launch Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
            return;
        }

        ProcessStartInfo launch = new ProcessStartInfo();
        launch.FileName        = "wscript.exe";
        launch.Arguments       = "\"" + vbsPath + "\"";
        launch.UseShellExecute = true;
        launch.WindowStyle     = ProcessWindowStyle.Hidden;
        Process.Start(launch);

        MessageBox.Show(
            "PizzaClub AI Server is starting in the background.\n\nDashboard will open in your browser shortly.",
            "PizzaClub - Starting",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        );
    }
}
"@

$CompilerParams = New-Object System.CodeDom.Compiler.CompilerParameters
$CompilerParams.GenerateExecutable = $true
$CompilerParams.OutputAssembly = "$ProjectRoot\PizzaClub.exe"
$CompilerParams.ReferencedAssemblies.Add("System.Windows.Forms.dll") | Out-Null
$CompilerParams.ReferencedAssemblies.Add("System.dll") | Out-Null
$CompilerParams.CompilerOptions = "/target:winexe /optimize+"

$IconPath = "$ProjectRoot\static\pizza_club_logo.ico"
if (Test-Path $IconPath) {
    $CompilerParams.CompilerOptions += " /win32icon:`"$IconPath`""
}

$Provider = New-Object Microsoft.CSharp.CSharpCodeProvider
$Result = $Provider.CompileAssemblyFromSource($CompilerParams, $CSharpCode)

if ($Result.Errors.Count -gt 0) {
    Write-Host "  [ERROR] C# Compilation failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK]   Launcher compiled." -ForegroundColor Green


# Step 2: Assemble regular files
Write-Host ""
Write-Host "  [2/4] Assembling application files..." -ForegroundColor Yellow

$Date = Get-Date -Format "yyyy-MM-dd_HHmmss"
$OutName = "PizzaClub_Standalone_$Date"
$StagingDir = "$ProjectRoot\$OutName"
$ZipPath = "$ProjectRoot\$OutName.zip"

if (Test-Path $StagingDir) { Remove-Item $StagingDir -Recurse -Force }
New-Item -ItemType Directory -Path $StagingDir | Out-Null

$FilesToCopy = @(
    "main.py",
    "PizzaClub.exe",
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
    "OPERATIONS_GUIDE.html",
    "SERVER_SETUP_GUIDE.html",
    "README_PIZZA_CLUB.html"
)

foreach ($f in $FilesToCopy) {
    $src = "$ProjectRoot\$f"
    if (Test-Path $src) {
        Copy-Item $src "$StagingDir\$f" -Force
    }
}

foreach ($folder in @("templates", "static")) {
    $src = "$ProjectRoot\$folder"
    if (Test-Path $src) {
        Copy-Item $src "$StagingDir\$folder" -Recurse -Force
    }
}

# Modify batch files in staging to point to the embedded python
$BatFiles = Get-ChildItem -Path $StagingDir -Filter "*.bat"
foreach ($bat in $BatFiles) {
    $content = Get-Content $bat.FullName
    $content = $content -replace "venv_311\\Scripts\\python.exe", "system\python.exe"
    Set-Content -Path $bat.FullName -Value $content
}


# Step 3: Embed Python & Site-Packages
Write-Host ""
Write-Host "  [3/4] Downloading & Embedding standalone Python 3.11..." -ForegroundColor Yellow

$SystemDir = "$StagingDir\system"
New-Item -ItemType Directory -Path $SystemDir | Out-Null
$PyZip = "$ProjectRoot\python-embed.zip"

if (-not (Test-Path $PyZip)) {
    Write-Host "    -> Downloading python-3.11.8-embed-amd64.zip from python.org..." -ForegroundColor DarkGray
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-amd64.zip" -OutFile $PyZip
}
else {
    Write-Host "    -> Using cached python-embed.zip" -ForegroundColor DarkGray
}

Write-Host "    -> Extracting Python..." -ForegroundColor DarkGray
Expand-Archive -Path $PyZip -DestinationPath $SystemDir -Force

Write-Host "    -> Configuring .pth to allow site-packages..." -ForegroundColor DarkGray
$PthFile = "$SystemDir\python311._pth"
$PthContent = @"
python311.zip
.
Lib\site-packages
import site
"@
Set-Content -Path $PthFile -Value $PthContent

Write-Host "    -> Copying bundled libraries from venv_311 (numpy, opencv, etc.)..." -ForegroundColor DarkGray
$VenvLib = "$ProjectRoot\venv_311\Lib\site-packages"
$TargetLib = "$SystemDir\Lib\site-packages"
New-Item -ItemType Directory -Path "$SystemDir\Lib" | Out-Null

# Robocopy for fast large folder copy
robocopy $VenvLib $TargetLib /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null

# Clean out unused cache and tests to reduce bloat
Remove-Item "$TargetLib\pip*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$TargetLib\setuptools*" -Recurse -Force -ErrorAction SilentlyContinue


# Step 4: Compress to ZIP
Write-Host ""
Write-Host "  [4/4] Compressing ultimate standalone ZIP... (this will take a minute)" -ForegroundColor Yellow

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
# Using .NET for larger/faster zip if it gets huge, but Compress-Archive is fine
Compress-Archive -Path "$StagingDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal

# Cleanup staging
Remove-Item $StagingDir -Recurse -Force

$ZipSize = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host "    ✅  STANDALONE PACKAGE COMPLETED" -ForegroundColor Green
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "    Output : $ZipPath" -ForegroundColor White
Write-Host "    Size   : $ZipSize MB" -ForegroundColor White
Write-Host ""
Write-Host "  100% STANDALONE. Python is NOT required on target." -ForegroundColor Cyan
Write-Host "  Zero installation process. Just extract and double click PizzaClub.exe!" -ForegroundColor Cyan
Write-Host ""
