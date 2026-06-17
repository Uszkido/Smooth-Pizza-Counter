$ErrorActionPreference = 'Stop'
$base = "C:\Users\COMPUTER 13\.gemini\antigravity\scratch\AI\smooth_pizza_counter"
$doneDir = "$base\Done"
$v3Dir = "$doneDir\PizzaClub_v3.0_Enterprise"

Write-Host "Creating Done\PizzaClub_v3.0_Enterprise directory..."
if (Test-Path $v3Dir) { Remove-Item -Recurse -Force $v3Dir }
if (!(Test-Path $doneDir)) { New-Item -ItemType Directory -Path $doneDir | Out-Null }
New-Item -ItemType Directory -Path $v3Dir | Out-Null

Write-Host "Copying fresh build files..."
# The build outputs to dist_v3\PizzaVMS (since spec is named PizzaVMS or the output is PizzaVMS)
if (Test-Path "$base\dist_v3\PizzaVMS") {
    Copy-Item -Recurse -Force "$base\dist_v3\PizzaVMS\*" $v3Dir
}
else {
    Write-Host "Build directory not found! Ensure PyInstaller finished successfully." -ForegroundColor Red
    exit 1
}

if (Test-Path "$v3Dir\PizzaVMS.exe") {
    Rename-Item "$v3Dir\PizzaVMS.exe" "PizzaClub.exe"
}

Write-Host "Copying management scripts and configs from v2.1..."
$v2Dir = "$base\dist\PizzaClub_v2.1_Enterprise"
$filesToCopy = @(
    "INSTALL_SERVICE.bat",
    "UNINSTALL_SERVICE.bat",
    "STATUS.bat",
    "WATCHDOG.bat",
    "STOP_SERVICE.bat",
    "START_HIDDEN.vbs",
    "CHANGE_PORT_AND_LAUNCH.bat",
    "START_REMOTE_ACCESS.bat",
    "config.json",
    "SERVER_SETUP_GUIDE.html",
    "UPGRADE_GUIDE_v2.1.html"
)

foreach ($f in $filesToCopy) {
    if (Test-Path "$v2Dir\$f") {
        Copy-Item "$v2Dir\$f" $v3Dir
    }
}

# Also manually copy ngrok if not copied
if (!(Test-Path "$v3Dir\ngrok.exe") -and (Test-Path "$v2Dir\ngrok.exe")) {
    Copy-Item "$v2Dir\ngrok.exe" $v3Dir
}

Write-Host "Updating v2.1 references to v3.0..."
# We will replace references inside bat, vbs, and html files
$textFiles = Get-ChildItem -Path $v3Dir -Include *.bat, *.vbs, *.html -Recurse

foreach ($file in $textFiles) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match "v2\.1") {
        $content = $content -replace "v2\.1", "v3.0"
        $content = $content -replace "2\.1\.0", "3.0.0"
        Set-Content -Path $file.FullName -Value $content -NoNewline
    }
}

# Rename the upgrade guide file
if (Test-Path "$v3Dir\UPGRADE_GUIDE_v2.1.html") {
    Rename-Item "$v3Dir\UPGRADE_GUIDE_v2.1.html" "UPGRADE_GUIDE_v3.0.html"
}

Write-Host "Zipping the result..."
$zipPath = "$doneDir\PizzaClub_v3.0_Enterprise.zip"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($v3Dir, $zipPath, [System.IO.Compression.CompressionLevel]::Fastest, $true)

Write-Host "V3 packaged successfully at $zipPath" -ForegroundColor Green
