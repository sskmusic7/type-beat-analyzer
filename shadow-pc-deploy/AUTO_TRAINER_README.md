# Type Beat Auto-Trainer

Autonomous training pipeline that processes artists every 4 hours without manual intervention.

## Setup (One-time)

1. **Right-click** `setup-task-admin.bat` and select **"Run as administrator"**
2. The task will be created in Windows Task Scheduler
3. Done! It will run automatically every 4 hours

## Schedule

Runs every 4 hours starting at 2:00 AM:
- 2:00 AM
- 6:00 AM
- 10:00 AM
- 2:00 PM
- 6:00 PM
- 10:00 PM

Each run processes up to 3 artists from the queue.

## What It Does

1. Checks the queue at `data/artist_queue.json`
2. If artists are pending, processes the next 3:
   - Downloads tracks from YouTube
   - Generates fingerprints
   - Creates DNA profiles
   - Uploads to GCS
   - Marks artists as completed
3. If queue is empty, exits immediately (no wasted resources)

## Monitoring

**Check status:**
```bash
python auto_trainer.py --stats
```

**View logs:**
- `auto_trainer.log` — detailed Python logs
- `auto_trainer_runs.log` — scheduled task run timestamps

**Manual run (test):**
```bash
start-auto-trainer.bat
```

Or via Task Scheduler:
```bash
schtasks /run /tn TypeBeatAutoTrainer
```

## Adding Artists to Queue

The queue is in `data/artist_queue.json`. To add artists:

```python
import json
from pathlib import Path

queue_path = Path("data/artist_queue.json")
queue = json.loads(queue_path.read_text())

# Add artists to pending
queue["pending"].extend([
    {"name": "Artist Name 1", "priority": 1},
    {"name": "Artist Name 2", "priority": 1}
])

queue_path.write_text(json.dumps(queue, indent=2))
```

Or use the script:
```bash
python auto_trainer.py --batch --artists "Drake,Future,Travis Scott"
```

## Modes

- `--daemon` — Process next N artists (for scheduled runs)
- `--batch --artists "X,Y,Z"` — Process specific artists
- `--discover` — Find new artists via Spotify Related Artists
- `--stats` — Show queue status
- `--dry-run` — Preview without training
- `--no-stems` — Skip stem separation (faster)

## Disable Auto-Trainer

Open Task Scheduler and disable/delete "TypeBeatAutoTrainer"

Or via command line:
```bash
schtasks /change /tn TypeBeatAutoTrainer /disable
```

## Troubleshooting

**Task not running?**
1. Check Task Scheduler → TypeBeatAutoTrainer → History tab
2. Verify webhook server is running: `curl http://localhost:8000/health`
3. Check network connectivity (requires internet for YouTube downloads)

**Queue stuck?**
- View queue: `python auto_trainer.py --stats`
- Clear failed: Edit `data/artist_queue.json` manually

**Out of disk space?**
- Auto-trainer cleans up audio files after processing
- Check `.cache/` directory size
- DNA profiles are ~50KB each, fingerprints ~10KB

## Architecture

```
Task Scheduler (every 4h)
        |
start-auto-trainer.bat
        |
auto_trainer.py --daemon --max-artists 3
        |
Reads artist_queue.json
        |
For each pending artist:
    1. HybridTrainer downloads from YouTube
    2. Generates fingerprint
    3. ArtistDNA creates profile
    4. Uploads to GCS
    5. Marks completed
        |
Writes logs to auto_trainer.log + auto_trainer_runs.log
```

---

**Created:** Apr 15, 2026
**Status:** Ready to deploy
**Zero AI tokens required** — fully autonomous Python pipeline
