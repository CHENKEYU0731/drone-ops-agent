param(
    [string]$PythonExe = "python",
    [string]$OutDir = "dist/release-check"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ResolvedOut = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $OutDir))
$TempBase = [System.IO.Path]::GetTempPath()
$TempRoot = Join-Path $TempBase ("drone-ops-release-" + [Guid]::NewGuid().ToString("N"))
$VenvRoot = Join-Path $TempRoot "venv"
$BuildDir = Join-Path $TempRoot "build"
$DemoDir = Join-Path $TempRoot "demo"

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
}

try {
    New-Item -ItemType Directory -Path $TempRoot | Out-Null
    Invoke-Checked $PythonExe @("-m", "venv", $VenvRoot)
    $VenvPython = Join-Path $VenvRoot "Scripts/python.exe"
    $EntryPoint = Join-Path $VenvRoot "Scripts/drone-ops.exe"

    Invoke-Checked $VenvPython @("-m", "pip", "install", "-c", (Join-Path $RepoRoot "constraints/release.txt"), "build==1.5.1", "setuptools==83.0.0", "wheel==0.47.0")
    Invoke-Checked $VenvPython @("-m", "pip", "install", "-c", (Join-Path $RepoRoot "constraints/dev.txt"), "-e", "${RepoRoot}[dev]")
    Invoke-Checked $VenvPython @((Join-Path $RepoRoot "scripts/check_environment.py"), "--out", (Join-Path $ResolvedOut "environment.json"), "--require-pass")
    Invoke-Checked $VenvPython @("-m", "pytest", $RepoRoot)
    Invoke-Checked $VenvPython @((Join-Path $RepoRoot "scripts/generate_demo_outputs.py"), "--out", $DemoDir)
    Invoke-Checked $VenvPython @("-m", "build", "--no-isolation", "--outdir", $BuildDir, $RepoRoot)

    $Wheel = Get-ChildItem -LiteralPath $BuildDir -Filter "*.whl" | Select-Object -First 1
    if (-not $Wheel) {
        throw "Wheel artifact was not generated."
    }
    Invoke-Checked $VenvPython @("-m", "pip", "uninstall", "-y", "drone-ops-agent")
    Invoke-Checked $VenvPython @("-m", "pip", "install", "--no-deps", $Wheel.FullName)
    Invoke-Checked $EntryPoint @("--help")
    Invoke-Checked $VenvPython @((Join-Path $RepoRoot "scripts/build_release_bundle.py"), "--source", $RepoRoot, "--out", $ResolvedOut)
    Write-Host "v2.4.0 release verification completed: $ResolvedOut"
}
finally {
    $FullTempRoot = [System.IO.Path]::GetFullPath($TempRoot)
    if ($FullTempRoot.StartsWith($TempBase, [System.StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $FullTempRoot)) {
        Remove-Item -LiteralPath $FullTempRoot -Recurse -Force
    }
}
