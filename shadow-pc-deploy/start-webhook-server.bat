@echo off
title Type Beat - Shadow PC Webhook Server
cd /d "C:\Users\Shadow\type-beat-analyzer\shadow-pc-deploy"
echo Starting Shadow PC Webhook Server on port 8000...
echo %date% %time% - Server starting >> shadow_pc_webhook.log
"C:\Users\Shadow\type-beat-analyzer\shadow-pc-deploy\venv\Scripts\python.exe" shadow_pc_webhook_server.py
