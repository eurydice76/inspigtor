@echo off

set target_dir=C:\Users\pellegrini\Temp\python-inspigtor

rmdir /S /Q %target_dir%

mkdir %target_dir%

C:\Users\pellegrini\packages\python-3.7.6-amd64.exe /quiet /uninstall

C:\Users\pellegrini\packages\python-3.7.6-amd64.exe /quiet TargetDir=%target_dir%

%pip_exe% install numpy
%pip_exe% install scipy
%pip_exe% install pandas
%pip_exe% install matplotlib
%pip_exe% install PyQt5

