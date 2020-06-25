@echo off

set current_dir=%cd%

set inspigtor_root_dir=C:\Users\pellegrini\git\inspigtor

set inspigtor_version=%1

set target_dir=C:\Users\pellegrini\Temp\python-inspigtor

set python_exe=%target_dir%\python.exe

cd %target_dir%\Lib\site-packages

rem cleanup previous installations
for /f %%i in ('dir /a:d /S /B inspigtor*') do rmdir /S /Q %%i
if exist %target_dir%\Scripts\inspigtor (
    del /Q %target_dir%\Scripts\inspigtor
)

cd %inspigtor_root_dir%

rem build and install inspigtor using the temporary python
%python_exe% setup.py build install

copy LICENSE %inspigtor_root_dir%\build_app\windows
copy CHANGELOG %inspigtor_root_dir%\build_app\windows\CHANGELOG.txt

set makensis="C:\Program Files (x86)\NSIS\Bin\makensis.exe"
set nsis_installer=%inspigtor_root_dir%\build_app\windows\inspigtor_installer.nsi

del /Q %target_dir%\inspigtor-%inspigtor_version%-win-amd64.exe

%makensis% /V4 /Onsis_log.txt /DVERSION=%inspigtor_version% /DARCH=win-amd64 /DTARGET_DIR=%target_dir% %nsis_installer%

cd %current_dir%