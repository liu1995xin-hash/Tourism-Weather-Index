<#!
.SYNOPSIS
Build the Tea Card single-file GUI executable with its frozen baseline embedded.

.DESCRIPTION
The active Python installation on this workstation uses a separate Tcl/Tk
resource directory. This script discovers that directory, exposes it to
PyInstaller, and then creates dist\TeaCardTourismIndex.exe.
#>

[CmdletBinding()]
param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

$tkInfo = @'
from pathlib import Path
import _tkinter
import tkinter

tcl_root = Path(tkinter.__file__).resolve().parents[2] / "tcl"
version = ".".join(_tkinter.TCL_VERSION.split(".")[:2])
print(tcl_root)
print(version)
'@ | & $Python -
if ($LASTEXITCODE -ne 0 -or $tkInfo.Count -ne 2) {
    throw "Unable to determine the Tcl/Tk resource directory from the selected Python interpreter."
}

$tclRoot = $tkInfo[0].Trim()
$tkVersion = $tkInfo[1].Trim()
$env:TCL_LIBRARY = Join-Path $tclRoot "tcl$tkVersion"
$env:TK_LIBRARY = Join-Path $tclRoot "tk$tkVersion"
if (-not (Test-Path $env:TCL_LIBRARY) -or -not (Test-Path $env:TK_LIBRARY)) {
    throw "Tcl/Tk library directories were not found: $env:TCL_LIBRARY ; $env:TK_LIBRARY"
}

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --optimize 2 `
    --name TeaCardTourismIndex `
    --add-data "data\baseline_tea_card_v2.xlsx;data" `
    .\src\tourism_index_gui.py
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$output = Join-Path $projectRoot "dist\TeaCardTourismIndex.exe"
if (-not (Test-Path $output)) {
    throw "The expected EXE was not generated: $output"
}

$file = Get-Item $output
Write-Host "EXE generated: $($file.FullName)"
Write-Host "Size: $([math]::Round($file.Length / 1MB, 2)) MB"
