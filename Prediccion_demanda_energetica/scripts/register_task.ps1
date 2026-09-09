param([string]$Hora = '08:00')
$ErrorActionPreference = 'Stop'
$raizProyecto = Split-Path -Parent $PSScriptRoot
$rutaGuion = Join-Path $PSScriptRoot 'run.ps1'
$accion = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -WindowStyle Hidden -File "' + $rutaGuion + '"') -WorkingDirectory $raizProyecto
$desencadenador = New-ScheduledTaskTrigger -Daily -At $Hora
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 4)
Register-ScheduledTask -TaskName 'Prediccion_demanda_energetica-Diaria' -Action $accion -Trigger $desencadenador -Settings $ajustes -Description 'Descarga, ETL y entrenamiento de demanda eléctrica. Requiere sesión iniciada.'
