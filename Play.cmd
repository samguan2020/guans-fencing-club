@echo off
if not defined UE_EDITOR set "UE_EDITOR=D:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
if not exist "%UE_EDITOR%" (
  echo Unreal Engine was not found. Update UE_EDITOR in this file.
  pause
  exit /b 1
)
start "Guan's Fencing Club" "%UE_EDITOR%" "%~dp0GuansFencingClub.uproject" /Game/GuansClub/FencingHall -game -windowed -ResX=1440 -ResY=900 -NoSplash -unattended
