# Testing Guide 🧪

This guide explains how to test the Type Beat Analyzer locally with the test tracks.

## Quick Start

### 1. Start Test Environment

Start both backend and frontend in one command:

```bash
./scripts/start_test_environment.sh
```

This will:
- Start backend on `http://localhost:8000`
- Start frontend on `http://localhost:3000`
- Wait for both to be ready
- Keep them running until you press Ctrl+C

### 2. Test Audio Files (Python Script)

Test all tracks with the Python test script:

```bash
# Single test run
python scripts/test_audio_files.py

# Continuous loop (for debugging)
python scripts/test_audio_files.py --loop
```

The script will:
- Test all MP3 files in `ref docs/tstt tracks]/`
- Show detailed results for each track
- Display matches, confidence scores, and trending data
- Retry failed requests automatically
- Provide a summary at the end

### 3. E2E Tests with Playwright

Install Playwright (first time only):

```bash
cd frontend
npm install
npx playwright install chromium
```

Run E2E tests:

```bash
# Run all tests
cd frontend
npm run test:e2e

# Run with UI (interactive)
npm run test:e2e:ui
```

## Test Tracks

Test tracks are located in: `ref docs/tstt tracks]/`

Current test tracks:
- `Trapic Rough - Prod by SSK.mp3`
- `Money Talks - Prod by SSK.mp3`
- `Expensive Habits - Prod. by SSK.mp3`
- `4 Loko - Prod. by SSK.mp3`
- `Kays' pain 2 (my whole life).mp3`
- `FEMA - Prod. by SSK.mp3`

## Manual Testing

### Test via Frontend UI

1. Start the test environment (see above)
2. Open `http://localhost:3000` in your browser
3. Drag and drop a test track onto the upload area
4. Wait for analysis to complete
5. Check results display

### Test via API Directly

```bash
# Test a single track
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@'ref docs/tstt tracks]/Trapic Rough - Prod by SSK.mp3'"

# Check backend health
curl http://localhost:8000/

# Get trending artists
curl http://localhost:8000/api/trending?limit=10
```

## Debugging

### Backend Logs

Backend logs are written to `backend_test.log` when using the start script.

Or run backend manually to see logs:

```bash
cd backend
python -m uvicorn main:app --port 8000
```

### Frontend Logs

Frontend logs are written to `frontend_test.log` when using the start script.

Or run frontend manually:

```bash
cd frontend
npm run dev
```

### Common Issues

**Backend not starting:**
- Check if port 8000 is already in use: `lsof -i :8000`
- Make sure conda environment is activated: `conda activate typebeat`
- Check backend dependencies: `pip list | grep -E "fastapi|uvicorn|librosa"`

**Frontend not starting:**
- Check if port 3000 is already in use: `lsof -i :3000`
- Make sure dependencies are installed: `cd frontend && npm install`
- Check for build errors: `npm run build`

**No matches found:**
- This is expected if the track isn't in the training database
- Check if fingerprint database has data: `curl http://localhost:8000/api/fingerprint/stats`
- The system only returns real matches (no fake predictions)

**Timeout errors:**
- Large audio files may take longer to process
- Increase timeout in test scripts if needed
- Check backend logs for processing errors

## Continuous Testing Loop

For debugging, run tests in a loop:

```bash
# Python script with loop
python scripts/test_audio_files.py --loop

# This will:
# - Test all tracks
# - Wait 10 seconds
# - Repeat indefinitely
# - Press Ctrl+C to stop
```

## Expected Results

### Successful Analysis
- Processing time: < 10 seconds for most files
- At least one match OR "No matches found" message
- Confidence scores between 0.0 and 1.0
- Trending data (if available) with rank, velocity, etc.

### Failed Analysis
- HTTP error status codes
- Error messages in response
- Check backend logs for details

## Performance Benchmarks

Expected processing times:
- Small files (< 5MB): 2-5 seconds
- Medium files (5-10MB): 5-10 seconds
- Large files (> 10MB): 10-20 seconds

If processing takes longer, check:
- Backend CPU/memory usage
- Network latency (if using external APIs)
- Audio file format/codec
