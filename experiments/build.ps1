# Builds experiments/*.exe with MinGW g++.
# MinGW is put first on PATH only while building (older libwinpthread-1.dll from iverilog etc. break cc1plus),
# and -static makes the .exe independent of PATH at run time.
# Usage (from any folder): .\experiments\build.ps1   or   .\experiments\build.ps1 -MinGW D:\other\mingw64\bin
param([string]$MinGW = 'C:\ProgramData\mingw64\mingw64\bin')

$oldPath = $env:PATH
$env:PATH = "$MinGW;$oldPath"
Push-Location $PSScriptRoot
$failed = $false
try {
    foreach ($name in 'bs_single', 'bs_trace', 'bs_team', 'flow_ref', 'cbm') {
        Write-Host "g++ -O3 -static -o $name.exe $name.cpp"
        & g++ -O3 -static -o "$name.exe" "$name.cpp"
        if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: $name" -ForegroundColor Red; $failed = $true }
    }
    # cbm with the rdtsc profile of the low level (week 6, archive/week6_part2.py)
    Write-Host "g++ -O3 -static -DBS_PROFILE -o cbm_prof.exe cbm.cpp"
    & g++ -O3 -static -DBS_PROFILE -o cbm_prof.exe cbm.cpp
    if ($LASTEXITCODE -ne 0) { Write-Host "FAILED: cbm_prof" -ForegroundColor Red; $failed = $true }
}
finally {
    Pop-Location
    $env:PATH = $oldPath
}
if ($failed) { exit 1 }
Write-Host 'Build OK' -ForegroundColor Green
