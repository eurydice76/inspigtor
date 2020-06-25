@echo off

set git_exe="C:\Program Files\Git\bin\git.exe"

set inspigtor_root_dir="C:\Users\pellegrini\git\inspigtor"

rem git clone and checkout inspigtor project
rmdir /S /Q %inspigtor_root_dir%
cd C:\Users\pellegrini\git
%git_exe% clone https://gitlab.com/eurydice38/inspigtor.git
cd %inspigtor_root_dir%
%git_exe% checkout %inspigtor_version%