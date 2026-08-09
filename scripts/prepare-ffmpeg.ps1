[CmdletBinding()]
param(
    [string]$TargetTriple = "x86_64-pc-windows-msvc"
)

$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $PSScriptRoot
$artifactRoot = Join-Path $workspace "development-artifacts\ffmpeg"
$archiveName = "ffmpeg-n8.1-latest-win64-lgpl-8.1.zip"
$archivePath = Join-Path $artifactRoot $archiveName
$extractRoot = Join-Path $artifactRoot "extracted"
$downloadUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/$archiveName"
$expectedArchiveSha256 = "9E7BA6E147252B33458786A3C1C2C9B337D21DA1AD53F5D98B1E98D9711E1A5B"
$binaryDirectory = Join-Path $workspace "apps\desktop\src-tauri\binaries"

New-Item -ItemType Directory -Path $artifactRoot, $extractRoot, $binaryDirectory -Force | Out-Null

if (-not (Test-Path -LiteralPath $archivePath)) {
    Write-Output "Downloading pinned LGPL FFmpeg runtime..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath
}

$archiveSha256 = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
if ($archiveSha256 -ne $expectedArchiveSha256) {
    throw "FFmpeg archive SHA256 mismatch. Expected $expectedArchiveSha256, got $archiveSha256"
}

Expand-Archive -LiteralPath $archivePath -DestinationPath $extractRoot -Force
$packageRoot = Get-ChildItem -LiteralPath $extractRoot -Directory |
    Where-Object { $_.Name -eq "ffmpeg-n8.1-latest-win64-lgpl-8.1" } |
    Select-Object -First 1
if (-not $packageRoot) {
    throw "The verified FFmpeg archive did not contain the expected package directory."
}

$ffmpeg = Join-Path $packageRoot.FullName "bin\ffmpeg.exe"
$ffprobe = Join-Path $packageRoot.FullName "bin\ffprobe.exe"
$license = Join-Path $packageRoot.FullName "LICENSE.txt"
foreach ($requiredFile in ($ffmpeg, $ffprobe, $license)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required FFmpeg file is missing: $requiredFile"
    }
}

$versionOutput = (& $ffmpeg -version 2>&1 | Out-String)
if ($versionOutput -match "--enable-gpl" -or $versionOutput -match "--enable-nonfree") {
    throw "Refusing to bundle an FFmpeg build with GPL or nonfree components enabled."
}
if ($versionOutput -notmatch "ffmpeg version n8\.1") {
    throw "Unexpected FFmpeg version in the verified archive."
}

Copy-Item -LiteralPath $ffmpeg -Destination (
    Join-Path $binaryDirectory "ffmpeg-$TargetTriple.exe"
) -Force
Copy-Item -LiteralPath $ffprobe -Destination (
    Join-Path $binaryDirectory "ffprobe-$TargetTriple.exe"
) -Force
Copy-Item -LiteralPath $license -Destination (
    Join-Path $binaryDirectory "ffmpeg-LICENSE.txt"
) -Force
Copy-Item -LiteralPath (Join-Path $workspace "THIRD_PARTY_NOTICES.md") -Destination (
    Join-Path $binaryDirectory "THIRD_PARTY_NOTICES.md"
) -Force

Write-Output "LGPL FFmpeg runtime ready in $binaryDirectory"
Write-Output "Archive SHA256: $archiveSha256"
