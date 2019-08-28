@echo off
for /l %%i in (0,1,12) do (
  echo [%%i] !date! !time! connected.
  start chrome.exe --new-window https://colab.research.google.com/drive/1SBINIp8MrW6KTmQ6LvvXsoZQadAa0jI_#scrollTo=8Juqgs-tW0wB
  timeout 3600 /nobreak >nul
)

pause
