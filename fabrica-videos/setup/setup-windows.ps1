<#
.SYNOPSIS
  Checks (and optionally installs) what the Fabrica Videos pipeline needs on Windows.

.DESCRIPTION
  Default mode only CHECKS and changes nothing.
  With -Install it offers to install missing tools through winget and asks before each one.
  It never installs CapCut, never touches API keys, and never downloads media.

.PARAMETER Install    Offer to install missing tools with winget (asks for each).
.PARAMETER WithNode   Also check/install Node.js LTS (needed later for Remotion graphics).
.PARAMETER SkipTests  Do not run the repository test suites at the end.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1
  powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1 -Install -WithNode
#>
[CmdletBinding()]
param(
  [switch]$Install,
  [switch]$WithNode,
  [switch]$SkipTests
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)   # ...\fabrica-videos
$installedSomething = $false
$results = New-Object System.Collections.ArrayList

function Add-Result($name, $status, $detail) {
  [void]$results.Add([pscustomobject]@{ Item = $name; Status = $status; Detail = $detail })
}

function Test-Command($name) {
  return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Get-PythonCommand {
  # Prefer the py launcher; ignore the Microsoft Store stub that opens the Store.
  if (Test-Command 'py') {
    try { & py -3 --version *> $null; if ($LASTEXITCODE -eq 0) { return @('py', '-3') } } catch { }
  }
  if (Test-Command 'python') {
    try {
      $v = & python --version 2>&1
      if ($LASTEXITCODE -eq 0 -and "$v" -match 'Python 3') { return @('python') }
    } catch { }
  }
  return $null
}

function Invoke-Python($pyCmd, [string[]]$arguments) {
  $exe = $pyCmd[0]
  $pre = @()
  if ($pyCmd.Count -gt 1) { $pre = $pyCmd[1..($pyCmd.Count - 1)] }
  & $exe @pre @arguments
}

function Install-WithWinget($id, $label) {
  if (-not (Test-Command 'winget')) {
    Write-Host "  winget is not available; install $label manually." -ForegroundColor Yellow
    return $false
  }
  $answer = Read-Host "  Install $label with winget ($id)? [y/N]"
  if ($answer -notmatch '^(y|s)') { Write-Host "  skipped."; return $false }
  & winget install --id $id -e --accept-package-agreements --accept-source-agreements
  if ($LASTEXITCODE -eq 0) { $script:installedSomething = $true; return $true }
  Write-Host "  winget exited with code $LASTEXITCODE." -ForegroundColor Yellow
  return $false
}

Write-Host "Fabrica Videos - Windows environment check" -ForegroundColor Cyan
Write-Host "Folder: $root"
if ($Install) { Write-Host "Mode: check + offer installs (you confirm each)" } else { Write-Host "Mode: check only (nothing is changed)" }
Write-Host ""

# --- Git ---------------------------------------------------------------------------------
if (Test-Command 'git') { Add-Result 'Git' 'OK' ((& git --version) -join ' ') }
else {
  Add-Result 'Git' 'MISSING' 'needed to clone and push the repository'
  if ($Install) { [void](Install-WithWinget 'Git.Git' 'Git') }
}

# --- Python ------------------------------------------------------------------------------
$py = Get-PythonCommand
if ($py) { Add-Result 'Python 3' 'OK' ((Invoke-Python $py @('--version')) -join ' ') }
else {
  Add-Result 'Python 3' 'MISSING' 'needed for the validator and the render script'
  if ($Install) { [void](Install-WithWinget 'Python.Python.3.12' 'Python 3.12') }
}

# --- FFmpeg / FFprobe --------------------------------------------------------------------
if ((Test-Command 'ffmpeg') -and (Test-Command 'ffprobe')) {
  Add-Result 'FFmpeg + FFprobe' 'OK' ((& ffmpeg -version | Select-Object -First 1) -join ' ')
} else {
  Add-Result 'FFmpeg + FFprobe' 'MISSING' 'needed to probe media and render review videos'
  if ($Install) { [void](Install-WithWinget 'Gyan.FFmpeg' 'FFmpeg') }
}

# --- Node.js (optional, Remotion later) --------------------------------------------------
if ($WithNode) {
  if (Test-Command 'node') { Add-Result 'Node.js' 'OK' ((& node --version) -join ' ') }
  else {
    Add-Result 'Node.js' 'MISSING' 'needed later for Remotion motion graphics'
    if ($Install) { [void](Install-WithWinget 'OpenJS.NodeJS.LTS' 'Node.js LTS') }
  }
}

# --- CapCut (never installed by this script) ---------------------------------------------
$capcutExe = Join-Path $env:LOCALAPPDATA 'CapCut\Apps\CapCut.exe'
$capcutDrafts = Join-Path $env:LOCALAPPDATA 'CapCut\User Data\Projects\com.lveditor.draft'
if (Test-Path $capcutExe) { Add-Result 'CapCut Desktop' 'OK' $capcutExe }
else { Add-Result 'CapCut Desktop' 'NOT FOUND' 'install it from capcut.com, or the path differs on your machine' }
if (Test-Path $capcutDrafts) { Add-Result 'CapCut drafts folder' 'OK' $capcutDrafts }
else { Add-Result 'CapCut drafts folder' 'NOT FOUND' 'open CapCut once and create a project, then re-run' }

# --- jsonschema (needed by the validator) ------------------------------------------------
if ($py) {
  $hasSchema = $false
  try { Invoke-Python $py @('-c', 'import jsonschema') *> $null; if ($LASTEXITCODE -eq 0) { $hasSchema = $true } } catch { }
  if ($hasSchema) { Add-Result 'Python: jsonschema' 'OK' 'installed' }
  else {
    Add-Result 'Python: jsonschema' 'MISSING' 'needed by timeline\validate_plan.py'
    if ($Install) {
      $answer = Read-Host "  Install jsonschema with pip (--user)? [y/N]"
      if ($answer -match '^(y|s)') { Invoke-Python $py @('-m', 'pip', 'install', '--user', 'jsonschema') }
    }
  }
}

Write-Host ""
$results | Format-Table -AutoSize | Out-String | Write-Host

if ($installedSomething) {
  Write-Host "Something was installed. Close this window, open a NEW PowerShell, and run this script again" -ForegroundColor Yellow
  Write-Host "so the updated PATH is picked up." -ForegroundColor Yellow
  exit 0
}

if (-not $py) { Write-Host "Python is missing; skipping probe and tests." -ForegroundColor Yellow; exit 1 }

Write-Host "Tool probe (workflow\probe_tools.py):" -ForegroundColor Cyan
Invoke-Python $py @((Join-Path $root 'workflow\probe_tools.py'))

if (-not $SkipTests) {
  Write-Host ""
  Write-Host "Running tests:" -ForegroundColor Cyan
  Invoke-Python $py @('-m', 'unittest', 'discover', '-s', (Join-Path $root 'timeline\tests'))
  Invoke-Python $py @('-m', 'unittest', 'discover', '-s', (Join-Path $root 'workflow\tests'))
}
