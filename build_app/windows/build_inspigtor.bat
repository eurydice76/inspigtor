@echo off

set inspigtor_version=%1

set target_dir=C:\Users\pellegrini\Temp\python_inspigtor

set python_exe=%target_dir%\python.exe

cd %target_dir%\Lib\site-packages

rem cleanup previous installations
for /f %i in ('dir /a:d /s /b inspigtor*') do rmdir /S /Q %i
del %target_dir%\Scripts\inspigtor

rmdir /S /Q C:\Users\pellegrini\git\inspigtor

rem git clone and checkout inspigtor project
cd C:\\Users\pellegrini\git
"C:\Program Files\Git\bin\git.exe" clone https://gitlab.com/eurydice38/inspigtor.git
cd inspigtor
"C:\Program Files\Git\bin\git.exe" checkout %inspigtor_version%

%python_exe% setup.py build
%python_exe% setup.py install
