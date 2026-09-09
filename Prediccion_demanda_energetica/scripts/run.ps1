$ErrorActionPreference = 'Stop'
$raizProyecto = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $raizProyecto
$ejecutablePython = Join-Path $raizProyecto '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $ejecutablePython)) { throw 'Se requiere crear .venv e instalar requirements.txt; las instrucciones figuran en README.md.' }
New-Item -ItemType Directory -Force -Path (Join-Path $raizProyecto 'logs') | Out-Null
$rutaRegistro = Join-Path $raizProyecto ('logs/run-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
Start-Transcript -Path $rutaRegistro
try {
    & $ejecutablePython -m energia ejecutar
    $codigoSalida = $LASTEXITCODE
} finally { Stop-Transcript }
exit $codigoSalida
