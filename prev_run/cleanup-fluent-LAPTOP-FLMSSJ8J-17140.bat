echo off
set LOCALHOST=%COMPUTERNAME%
set KILL_CMD="C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v252\fluent/ntbin/win64/winkill.exe"

start "tell.exe" /B "C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v252\fluent\ntbin\win64\tell.exe" LAPTOP-FLMSSJ8J 52337 CLEANUP_EXITING
timeout /t 1
"C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v252\fluent\ntbin\win64\kill.exe" tell.exe
if /i "%LOCALHOST%"=="LAPTOP-FLMSSJ8J" (%KILL_CMD% 29168) 
if /i "%LOCALHOST%"=="LAPTOP-FLMSSJ8J" (%KILL_CMD% 17140) 
if /i "%LOCALHOST%"=="LAPTOP-FLMSSJ8J" (%KILL_CMD% 27636)
del "C:\ANSYS PROJ\cleanup-fluent-LAPTOP-FLMSSJ8J-17140.bat"
