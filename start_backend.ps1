$env:PYTHONPATH = "$PSScriptRoot\backend"
$env:DISABLE_SQLALCHEMY_CEXT = "1"
Set-Location "$PSScriptRoot\backend"
& ".\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

