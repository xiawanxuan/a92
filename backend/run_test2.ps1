$pyExe = "C:\Users\User\AppData\Local\Microsoft\WindowsApps\python.exe"
$scriptPath = "app\ml\test_grad_cam.py"

Write-Host "Attempting to run Python script..."
Write-Host "Python path: $pyExe"
Write-Host "Script path: $scriptPath"
Write-Host ""

& $pyExe $scriptPath
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "Exit code: $exitCode"
exit $exitCode
