@echo off
echo Checking Python dependencies...
python check_deps.py
echo.
echo Running Grad-CAM tests...
python app\ml\test_grad_cam.py
echo.
echo Test exit code: %ERRORLEVEL%
