@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_tools\bridge\killswitch.ps1" kill
