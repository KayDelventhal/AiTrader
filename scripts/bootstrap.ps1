$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$nodeVersion = 'v24.22.1'
$nodeArchive = "node-$nodeVersion-win-x64.zip"
$toolsDirectory = Join-Path $repo '.tools'
New-Item -ItemType Directory -Force -Path $toolsDirectory | Out-Null
$nodeDirectory = Join-Path $toolsDirectory "node-$nodeVersion-win-x64"
if (-not (Test-Path -LiteralPath (Join-Path $nodeDirectory 'node.exe'))) {
    $archivePath = Join-Path $toolsDirectory $nodeArchive
    Invoke-WebRequest -UseBasicParsing -Uri "https://nodejs.org/dist/$nodeVersion/$nodeArchive" -OutFile $archivePath
    $checksumText = (Invoke-WebRequest -UseBasicParsing -Uri "https://nodejs.org/dist/$nodeVersion/SHASUMS256.txt").Content
    $expectedHash = ($checksumText -split "`n" | Where-Object { $_.Trim().EndsWith($nodeArchive) }) -split '\s+' | Select-Object -First 1
    if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash -ne $expectedHash) { throw 'Node checksum mismatch' }
    Expand-Archive -LiteralPath $archivePath -DestinationPath $toolsDirectory
}
$env:PATH = $nodeDirectory + ';' + $env:PATH
& (Join-Path $nodeDirectory 'npm.cmd') install --prefix $toolsDirectory pnpm@10.28.2 --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw 'pnpm installation failed' }
& (Join-Path $toolsDirectory 'node_modules\.bin\pnpm.cmd') --dir frontend install --frozen-lockfile
if ($LASTEXITCODE -ne 0) { throw 'Frontend installation failed' }
Write-Output 'Workspace-local Node and pnpm are ready. System PATH was not changed.'
