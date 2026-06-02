param(
    [string]$OutputPath = "dist\EduChain-source.zip"
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$distRoot = Join-Path $projectRoot "dist"
$stageRoot = Join-Path $distRoot "EduChain-source"
$resolvedDist = if (Test-Path $distRoot) { (Resolve-Path $distRoot).Path } else { $distRoot }

if (-not (Test-Path $distRoot)) {
    New-Item -ItemType Directory -Path $distRoot | Out-Null
}

if (Test-Path $stageRoot) {
    $resolvedStage = (Resolve-Path $stageRoot).Path
    if (-not $resolvedStage.StartsWith((Resolve-Path $distRoot).Path)) {
        throw "Refusing to remove unexpected path: $resolvedStage"
    }
    Remove-Item -LiteralPath $stageRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $stageRoot | Out-Null

$excludeDirs = @(
    ".git",
    ".agents",
    ".claude",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache"
)

$excludeFiles = @(
    "AGENTS.md",
    "CLAUDE.md",
    "backend\.env",
    "*.pyc",
    "*.pyo",
    "*.log",
    ".DS_Store"
)

function Get-ProjectRelativePath {
    param([string]$FullName)

    $fullPath = [System.IO.Path]::GetFullPath($FullName)
    $rootPath = [System.IO.Path]::GetFullPath($projectRoot).TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside project root: $fullPath"
    }
    return $fullPath.Substring($rootPath.Length)
}

function Should-SkipPath {
    param([string]$FullName)

    $relative = Get-ProjectRelativePath $FullName
    $parts = $relative -split '[\\/]'

    foreach ($dir in $excludeDirs) {
        if ($parts -contains $dir) {
            return $true
        }
    }

    foreach ($pattern in $excludeFiles) {
        if ($relative -like $pattern) {
            return $true
        }
    }

    if ($relative -like "backend\uploads\*" -and $relative -ne "backend\uploads\.gitkeep") {
        return $true
    }

    return $false
}

$items = Get-ChildItem -LiteralPath $projectRoot -Recurse -Force
foreach ($item in $items) {
    if (Should-SkipPath $item.FullName) {
        continue
    }

    $relative = Get-ProjectRelativePath $item.FullName
    $target = Join-Path $stageRoot $relative

    if ($item.PSIsContainer) {
        if (-not (Test-Path $target)) {
            New-Item -ItemType Directory -Path $target | Out-Null
        }
    }
    else {
        $targetParent = Split-Path -Parent $target
        if (-not (Test-Path $targetParent)) {
            New-Item -ItemType Directory -Path $targetParent | Out-Null
        }
        Copy-Item -LiteralPath $item.FullName -Destination $target -Force
    }
}

$zipPath = Join-Path $projectRoot $OutputPath
$zipParent = Split-Path -Parent $zipPath
if (-not (Test-Path $zipParent)) {
    New-Item -ItemType Directory -Path $zipParent | Out-Null
}
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -Path (Join-Path $stageRoot "*") -DestinationPath $zipPath -Force
Write-Host "Packaged source archive: $zipPath"
