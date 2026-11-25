[CmdletBinding()]
param(
    [string]$CondaEnvironment = "study-assistant",
    [string]$TargetTriple = "x86_64-pc-windows-msvc"
)

$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $PSScriptRoot
$temporaryRoot = Join-Path $workspace "development-artifacts\pyinstaller"
$distribution = Join-Path $temporaryRoot "dist"
$work = Join-Path $temporaryRoot "work"
$spec = Join-Path $temporaryRoot "spec"
$binaryDirectory = Join-Path $workspace "apps\desktop\src-tauri\binaries"
$target = Join-Path $binaryDirectory "study-assistant-agent-$TargetTriple.exe"

if (Test-Path -LiteralPath $temporaryRoot) {
    $resolvedTemporaryRoot = (Resolve-Path -LiteralPath $temporaryRoot).Path
    $expectedParent = (Resolve-Path -LiteralPath (Join-Path $workspace "development-artifacts")).Path
    if (-not $resolvedTemporaryRoot.StartsWith($expectedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean a path outside development-artifacts: $resolvedTemporaryRoot"
    }
    Remove-Item -LiteralPath $resolvedTemporaryRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $distribution, $work, $spec, $binaryDirectory -Force | Out-Null

Push-Location $workspace
try {
    conda run -n $CondaEnvironment python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --noconsole `
        --name study-assistant-agent `
        --distpath $distribution `
        --workpath $work `
        --specpath $spec `
        --paths (Join-Path $workspace "services\agent\src") `
        --collect-data yt_dlp `
        --collect-all faster_whisper `
        --collect-all ctranslate2 `
        --collect-all onnxruntime `
        --collect-all tokenizers `
        --collect-all huggingface_hub `
        --collect-all hf_xet `
        --collect-submodules keyring.backends `
        --hidden-import uvicorn.logging `
        --hidden-import uvicorn.loops.auto `
        --hidden-import uvicorn.protocols.http.auto `
        --hidden-import uvicorn.protocols.websockets.auto `
        --hidden-import uvicorn.lifespan.on `
        (Join-Path $workspace "scripts\agent_sidecar_entry.py")
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }

    conda run -n $CondaEnvironment python scripts/collect-pyav-notices.py $binaryDirectory
    if ($LASTEXITCODE -ne 0) {
        throw "Could not collect the PyAV license and native library build information."
    }

    Copy-Item -LiteralPath (Join-Path $distribution "study-assistant-agent.exe") -Destination $target -Force
    Write-Output "Sidecar ready: $target"
}
finally {
    Pop-Location
}
