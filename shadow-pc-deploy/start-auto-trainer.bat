@echo off
cd /d "C:\Users\Shadow\type-beat-analyzer\shadow-pc-deploy"
echo [%date% %time%] Auto-trainer started >> auto_trainer_runs.log
"venv\Scripts\python.exe" auto_trainer.py --daemon --max-artists 3 >> auto_trainer_runs.log 2>&1
echo [%date% %time%] Auto-trainer finished >> auto_trainer_runs.log
