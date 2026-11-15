$env:PATH = "C:\Program Files\nodejs;" + $env:PATH
Set-Location "$PSScriptRoot\frontend"
& "C:\Program Files\nodejs\npm.cmd" run dev -- --host 127.0.0.1

