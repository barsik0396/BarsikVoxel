@echo off
chcp 65001
::
::  BGP - Авто-скрипт для отправки на github
::                Версия 1.0
::
git add .
git commit -m "Обновил файлы через BGP 1.0"
git push