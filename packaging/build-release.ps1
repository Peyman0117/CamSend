[CmdletBinding()]
param(
    [switch]$SkipDependencyInstall,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

function Get-ProjectChildPath {
    param([Parameter(Mandatory = $true)][string]$Child)

    $fullPath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $Child))
    $requiredPrefix = $projectRoot.TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith($requiredPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Generated path is outside the CamSend project: $fullPath"
    }
    return $fullPath
}

function Assert-LastExitCode {
    param([Parameter(Mandatory = $true)][string]$Action)

    if ($LASTEXITCODE -ne 0) {
        throw "$Action failed with exit code $LASTEXITCODE."
    }
}

$versionSource = Get-Content -Raw -Encoding UTF8 (Join-Path $projectRoot "camsend_version.py")
if ($versionSource -notmatch 'VERSION\s*=\s*"(?<version>\d+\.\d+\.\d+)"') {
    throw "Could not read VERSION from camsend_version.py."
}
$version = $Matches.version
# Guard against publishing a build whose release notes still describe another version.
$releaseNotes = Get-Content -Raw -Encoding UTF8 (Join-Path $projectRoot "packaging\release-notes.md")
if ($releaseNotes -notmatch "(?m)^# CamSend $([regex]::Escape($version))\s*$") {
    throw "packaging/release-notes.md does not start with '# CamSend $version'. Update the release notes first."
}

$buildDir = Get-ProjectChildPath "build"
$distDir = Get-ProjectChildPath "dist"
$releaseDir = Get-ProjectChildPath "release"
$venvDir = Get-ProjectChildPath ".venv-build"
$buildPython = Join-Path $venvDir "Scripts\python.exe"

Set-Location -LiteralPath $projectRoot

if (-not (Test-Path -LiteralPath $buildPython)) {
    # The official build uses Python 3.12 (see BUILDING.md); prefer it via the py launcher.
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        & $pyLauncher.Source -V:3.12 -c "pass" 2>$null
    }
    if ($pyLauncher -and $LASTEXITCODE -eq 0) {
        & $pyLauncher.Source -V:3.12 -m venv $venvDir
    } else {
        python -m venv $venvDir
    }
    Assert-LastExitCode "Creating the build virtual environment"
}

if (-not $SkipDependencyInstall) {
    & $buildPython -m pip install --disable-pip-version-check --requirement (Join-Path $projectRoot "requirements-build.lock")
    Assert-LastExitCode "Installing build dependencies"
}

# Python 3.14 ships Tcl/Tk 9, whose data lives inside the DLL. PyInstaller's tkinter
# runtime hook still expects a _tcl_data folder, so such a CamSend.exe fails at start.
& $buildPython -c "import sys, tkinter; sys.exit(0 if tkinter.TclVersion < 9 else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "The build Python uses Tcl/Tk 9, which produces a CamSend.exe that cannot start. Delete .venv-build and install Python 3.12 (py install 3.12)."
}

foreach ($generatedPath in @($buildDir, $distDir, $releaseDir)) {
    if (Test-Path -LiteralPath $generatedPath) {
        Remove-Item -LiteralPath $generatedPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $generatedPath | Out-Null
}

& $buildPython -m unittest discover -s tests -v
Assert-LastExitCode "Running the release test suite"

$logoPath = Join-Path $projectRoot "static\brand\camsend-logo.png"
$iconPath = Join-Path $buildDir "camsend.ico"
& $buildPython (Join-Path $projectRoot "packaging\create_icon.py") $logoPath $iconPath
Assert-LastExitCode "Creating the Windows icon"

$versionParts = $version.Split('.')
$versionInfo = @"
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($($versionParts[0]), $($versionParts[1]), $($versionParts[2]), 0),
    prodvers=($($versionParts[0]), $($versionParts[1]), $($versionParts[2]), 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'CamSend Project'),
         StringStruct('FileDescription', 'CamSend Local'),
         StringStruct('FileVersion', '$version'),
         StringStruct('InternalName', 'CamSend'),
         StringStruct('OriginalFilename', 'CamSend.exe'),
         StringStruct('ProductName', 'CamSend'),
         StringStruct('ProductVersion', '$version')]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@
$versionInfoPath = Join-Path $buildDir "version_info.txt"
Set-Content -LiteralPath $versionInfoPath -Value $versionInfo -Encoding ASCII

& $buildPython -m PyInstaller --noconfirm --clean --distpath $distDir --workpath (Join-Path $buildDir "pyinstaller") (Join-Path $projectRoot "packaging\CamSend.spec")
Assert-LastExitCode "Building CamSend with PyInstaller"

$appDir = Join-Path $distDir "CamSend"
$appExe = Join-Path $appDir "CamSend.exe"
if (-not (Test-Path -LiteralPath $appExe)) {
    throw "PyInstaller completed without producing $appExe."
}

foreach ($document in @("LICENSE", "TRADEMARKS.md", "README.md")) {
    Copy-Item -LiteralPath (Join-Path $projectRoot $document) -Destination (Join-Path $appDir $document) -Force
}

$portableZip = Join-Path $releaseDir "CamSend-Portable-$version.zip"
Compress-Archive -Path (Join-Path $appDir "*") -DestinationPath $portableZip -CompressionLevel Optimal

$installerPath = $null
if (-not $SkipInstaller) {
    $compilerCandidates = @(
        $env:INNO_SETUP_COMPILER,
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        # winget installs Inno Setup per user when the shell is not elevated.
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe")
    ) | Where-Object { $_ }

    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) {
        $compilerCandidates = @($command.Source) + $compilerCandidates
    }
    $iscc = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $iscc) {
        throw "Inno Setup Compiler (ISCC.exe) was not found. Install Inno Setup or rerun with -SkipInstaller."
    }

    & $iscc "/DMyAppVersion=$version" "/O$releaseDir" "/FCamSend-Setup-$version" (Join-Path $projectRoot "packaging\installer\CamSend.iss")
    Assert-LastExitCode "Building the Windows installer"
    $installerPath = Join-Path $releaseDir "CamSend-Setup-$version.exe"
    if (-not (Test-Path -LiteralPath $installerPath)) {
        throw "Inno Setup completed without producing $installerPath."
    }
}

$artifacts = @($portableZip)
if ($installerPath) {
    $artifacts += $installerPath
}
$hashLines = foreach ($artifact in $artifacts) {
    $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $artifact
    "$($hash.Hash.ToLowerInvariant())  $([System.IO.Path]::GetFileName($artifact))"
}
$hashFile = Join-Path $releaseDir "SHA256SUMS.txt"
Set-Content -LiteralPath $hashFile -Value $hashLines -Encoding ASCII

Write-Host ""
Write-Host "CamSend $version build completed:" -ForegroundColor Green
Get-Item -LiteralPath ($artifacts + $hashFile) | Select-Object Name, Length, LastWriteTime
