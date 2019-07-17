@ECHO OFF

python3 -m venv py_env 
if %ERRORLEVEL% neq 0 goto PythonVenvFallthrough
goto ACTIVATE

:PythonVenvFallthrough
echo 'python3' command failed - attempting virtual environment setup with 'python' instead
python -m venv py_env

if %ERRORLEVEL% == 0 goto ACTIVATE
echo No Python install in PATH - failed to set up the environment
exit /b 1



:ACTIVATE
echo Activating python virtual environment
CALL .\py_env\Scripts\activate.bat



:INSTALL_REQ
echo Installing python requirements
pip install -r requirements.txt
