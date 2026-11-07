<#
  install_ngombe_task.ps1 - register the scheduled task "Ngombe line watcher": the always-on loop that answers the
  cattle records app's traffic on the Zamai line within seconds (tools/zamai_line/ngombe_watch.py). Starts at logon
  and is re-tried every 5 minutes; IgnoreNew keeps a single instance, no time limit, pythonw.exe so no window.

  Run:     powershell -ExecutionPolicy Bypass -File tools\zamai_line\install_ngombe_task.ps1
  Remove:  schtasks /Delete /TN "Ngombe line watcher" /F
  Stop:    schtasks /End /TN "Ngombe line watcher"   (it comes back within 5 minutes unless the task is disabled:
           schtasks /Change /TN "Ngombe line watcher" /DISABLE)
#>
$ErrorActionPreference = "Stop"
$name = "Ngombe line watcher"
$pyw = Join-Path $env:USERPROFILE "python312\pythonw.exe"
if (-not (Test-Path $pyw)) { Write-Error "pythonw.exe not found"; exit 1 }
$script = Join-Path $PSScriptRoot "ngombe_watch.py"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$action  = New-ScheduledTaskAction -Execute $pyw -Argument "-X utf8 `"$script`"" -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$logon   = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
            -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
Register-ScheduledTask -TaskName $name -Action $action -Trigger @($trigger, $logon) -Principal $principal `
  -Settings $settings -Description "Ng'ombe line watcher: answers the cattle records app's messages on the Zamai line within seconds, no model. tools/zamai_line/ngombe_watch.py" -Force | Out-Null
Start-ScheduledTask -TaskName $name
Write-Output "registered and started '$name': at logon and every 5 min (single instance), $pyw $script"
