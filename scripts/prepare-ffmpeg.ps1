[CmdletBinding()]
param(
    [string]$TargetTriple = "x86_64-pc-windows-msvc"
)

$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $PSScriptRoot
$artifactRoot = Join-Path $workspace "development-artifacts\ffmpeg"
$releaseTag = "autobuild-2026-11-24-12-41"
$packageName = "ffmpeg-n8.1.3-41-ga8029b6528-win64-lgpl-8.1"
$archiveName = "$packageName.zip"
$archivePath = Join-Path $artifactRoot $archiveName
$extractRoot = Join-Path $artifactRoot "extracted"
$downloadUrl = "https://github.com/FFmpeg-Builds/FFmpeg-Builds/releases/download/$releaseTag/$archiveName"
$expectedArchiveSha256 = "2201DF4D6CBDCBBDA9E612645605735821BB4CD0B120A9683F970C4C4E2DE8E4"
$binaryDirectory = Join-Path $workspace "apps\desktop\src-tauri\binaries"

New-Item -ItemType Directory -Path $artifactRoot, $extractRoot, $binaryDirectory -Force | Out-Null

$candidate = $archivePath
if (-not (Test-Path -LiteralPath $archivePath -PathType Leaf)) {
    $candidate = "$archivePath.download"
    Write-Output "Downloading pinned LGPL FFmpeg runtime from $releaseTag..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $candidate
}

$archiveSha256 = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash
if ($archiveSha256 -ne $expectedArchiveSha256) {
    throw "FFmpeg archive SHA256 mismatch. Expected $expectedArchiveSha256, got $archiveSha256"
}
if ($candidate -ne $archivePath) {
    Move-Item -LiteralPath $candidate -Destination $archivePath
}

Expand-Archive -LiteralPath $archivePath -DestinationPath $extractRoot -Force
$packageRoot = Join-Path $extractRoot $packageName
if (-not (Test-Path -LiteralPath $packageRoot -PathType Container)) {
    throw "The verified FFmpeg archive did not contain the expected package directory."
}

$ffmpeg = Join-Path $packageRoot "bin\ffmpeg.exe"
$ffprobe = Join-Path $packageRoot "bin\ffprobe.exe"
$license = Join-Path $packageRoot "LICENSE.txt"
foreach ($requiredFile in ($ffmpeg, $ffprobe, $license)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required FFmpeg file is missing: $requiredFile"
    }
}

$versionOutput = (& $ffmpeg -version 2>&1 | Out-String)
if ($versionOutput -match "--enable-gpl" -or $versionOutput -match "--enable-nonfree") {
    throw "Refusing to bundle an FFmpeg build with GPL or nonfree components enabled."
}
if ($LASTEXITCODE -ne 0 -or $versionOutput -notmatch "ffmpeg version n8\.1\.3-41-ga8029b6528\b") {
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
$versionOutput | Set-Content -LiteralPath (Join-Path $binaryDirectory "ffmpeg-build.txt") -Encoding utf8
Copy-Item -LiteralPath (Join-Path $workspace "THIRD_PARTY_NOTICES.md") -Destination (
    Join-Path $binaryDirectory "THIRD_PARTY_NOTICES.md"
) -Force

Write-Output "LGPL FFmpeg runtime ready in $binaryDirectory"
Write-Output "Archive SHA256: $archiveSha256"
