@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\bridge\bridge.ps1" %*
