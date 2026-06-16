$pythonPath = "C:\Users\User\AppData\Local\Microsoft\WindowsApps\python.exe"
$args1 = "check_deps.py"
$args2 = "app\ml\test_grad_cam.py"

Write-Host "Checking Python dependencies..."
& $pythonPath $args1
$depsExitCode = $LASTEXITCODE
Write-Host "Deps check exit code: $depsExitCode"

Write-Host ""
Write-Host "Running Grad-CAM tests..."
& $pythonPath $args2
$testExitCode = $LASTEXITCODE
Write-Host "Test exit code: $testExitCode"

exit $testExitCode
