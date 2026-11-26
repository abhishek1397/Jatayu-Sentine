@echo off
echo Stopping only the JATAYU command prompt windows...

:: /IM cmd.exe ensures we only touch command prompts, ignoring Chrome/other apps
:: /FI filters for our specific window titles
taskkill /F /FI "WINDOWTITLE eq Jatayu*" /IM cmd.exe /T

:: Close this terminal window automatically
exit