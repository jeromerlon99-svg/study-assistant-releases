[CmdletBinding()]
param(
    [string]$CondaEnvironment = "study-assistant"
)

$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent $PSScriptRoot
$artifacts = Join-Path $workspace "development-artifacts"
$testArtifacts = Join-Path $artifacts "tests"
$cargoTarget = Join-Path $artifacts "cargo-target"
$testData = Join-Path $artifacts "runtime-data"
$ruffCache = Join-Path $artifacts "ruff-cache"

New-Item -ItemType Directory -Path $testArtifacts, $cargoTarget, $testData, $ruffCache -Force | Out-Null

$env:STUDY_ASSISTANT_DATA_DIR = $testData
$env:STUDY_ASSISTANT_SEMANTIC_AUTO_INITIALIZE = "false"
$env:CARGO_TARGET_DIR = $cargoTarget
$env:CI = "true"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host "==> $Label"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Push-Location $workspace
try {
    Invoke-Checked "Version consistency" {
        conda run --no-capture-output -n $CondaEnvironment node scripts/check-version.mjs
    }
    Invoke-Checked "Python dependency integrity" {
        conda run --no-capture-output -n $CondaEnvironment python -m pip check
    }
    Invoke-Checked "Python lint" {
        conda run --no-capture-output -n $CondaEnvironment `
            python -m ruff check services/agent/src tests/agent --cache-dir $ruffCache
    }
    Invoke-Checked "Python tests" {
        conda run --no-capture-output -n $CondaEnvironment python -m pytest tests/agent -q `
            -o "cache_dir=$testArtifacts\pytest-cache" `
            --basetemp (Join-Path $testArtifacts "pytest-temp") `
            --junitxml (Join-Path $testArtifacts "pytest.xml")
    }
    Invoke-Checked "Frontend production build" {
        conda run --no-capture-output -n $CondaEnvironment pnpm build
    }
    Invoke-Checked "Rust formatting" {
        cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
    }
    Invoke-Checked "Rust Clippy" {
        cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml `
            --features custom-protocol -- -D warnings
    }
}
finally {
    Pop-Location
}

Write-Host "All checks passed. Disposable reports are in development-artifacts/."
