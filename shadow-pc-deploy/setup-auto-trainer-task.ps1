# Type Beat Auto-Trainer - Task Scheduler Setup
# Run this as Administrator

$ErrorActionPreference = "Stop"

Write-Host "Setting up Type Beat Auto-Trainer scheduled task..." -ForegroundColor Cyan

# Task configuration
$taskName = "TypeBeatAutoTrainer"
$batFile = "C:\Users\Shadow\type-beat-analyzer\shadow-pc-deploy\start-auto-trainer.bat"
$workingDir = "C:\Users\Shadow\type-beat-analyzer\shadow-pc-deploy"
$description = "Autonomous training pipeline for Type Beat Analyzer - processes 3 artists every 4 hours"

# Create action
$action = New-ScheduledTaskAction -Execute $batFile -WorkingDirectory $workingDir

# Create trigger (daily at 2 AM, repeat every 4 hours)
$trigger = New-ScheduledTaskTrigger -Daily -At "02:00"
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At "02:00" -RepetitionInterval (New-TimeSpan -Hours 4)).Repetition

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

# Principal (run as Shadow user, highest privileges)
$principal = New-ScheduledTaskPrincipal -UserId "Shadow" -LogonType S4U -RunLevel Highest

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task already exists. Unregistering..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description $description

Write-Host "`nTask created successfully!" -ForegroundColor Green
Write-Host "`nSchedule: Runs every 4 hours starting at 2:00 AM" -ForegroundColor Cyan
Write-Host "Next runs: 2:00 AM, 6:00 AM, 10:00 AM, 2:00 PM, 6:00 PM, 10:00 PM" -ForegroundColor Cyan
Write-Host "`nTo verify: Open Task Scheduler and look for 'TypeBeatAutoTrainer'" -ForegroundColor Cyan
Write-Host "To run manually: Right-click the task and select 'Run'" -ForegroundColor Cyan
Write-Host "To test now: schtasks /run /tn TypeBeatAutoTrainer" -ForegroundColor Cyan

# Show task info
Write-Host "`nTask details:" -ForegroundColor Yellow
Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State, Description
