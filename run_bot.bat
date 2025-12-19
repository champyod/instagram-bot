@echo off
title Instagram DM Bot
:loop
echo Starting Bot...
python bot.py
echo Bot crashed or stopped. Restarting in 10 seconds...
timeout /t 10
goto loop
