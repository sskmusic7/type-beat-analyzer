#!/usr/bin/env python3
"""
Test script to analyze all test tracks and verify results
Runs in loop to debug until clear results are shown
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Test tracks directory
TEST_TRACKS_DIR = Path("/Users/sskmusic/Type beat/ref docs/tstt tracks]")
BACKEND_URL = "http://localhost:8000"
MAX_RETRIES = 3
RETRY_DELAY = 2


def check_backend_health() -> bool:
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Backend not available: {e}")
        return False


def analyze_track(track_path: Path) -> Optional[Dict]:
    """Analyze a single track"""
    print(f"\n{'='*60}")
    print(f"🎵 Testing: {track_path.name}")
    print(f"{'='*60}")
    
    if not track_path.exists():
        print(f"❌ File not found: {track_path}")
        return None
    
    file_size = track_path.stat().st_size / (1024 * 1024)  # MB
    print(f"📁 File size: {file_size:.2f} MB")
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"⏳ Uploading and analyzing (attempt {attempt + 1}/{MAX_RETRIES})...")
            
            with open(track_path, 'rb') as f:
                files = {'file': (track_path.name, f, 'audio/mpeg')}
                response = requests.post(
                    f"{BACKEND_URL}/api/analyze",
                    files=files,
                    timeout=60  # 60 second timeout for large files
                )
            
            if response.status_code == 200:
                result = response.json()
                processing_time = result.get('processing_time_ms', 0)
                matches = result.get('matches', [])
                
                print(f"✅ Analysis complete in {processing_time:.2f}ms")
                print(f"📊 Found {len(matches)} match(es)")
                
                if matches:
                    print("\n🎯 Matches:")
                    for i, match in enumerate(matches, 1):
                        artist = match.get('artist', 'Unknown')
                        confidence = match.get('confidence', 0) * 100
                        trending = match.get('trending')
                        
                        print(f"  {i}. {artist} - {confidence:.1f}% confidence")
                        
                        if trending:
                            trend_dir = trending.get('trend_direction', 'stable')
                            rank = trending.get('rank', 'N/A')
                            velocity = trending.get('velocity', 0)
                            print(f"     📈 Trending: {trend_dir} | Rank: #{rank} | Velocity: {velocity:.0f} views/day")
                else:
                    print("⚠️  No matches found - track may not be in database")
                
                return {
                    'file': track_path.name,
                    'success': True,
                    'matches': len(matches),
                    'processing_time_ms': processing_time,
                    'results': matches
                }
            else:
                error_detail = response.json().get('detail', 'Unknown error') if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"❌ Error {response.status_code}: {error_detail}")
                
                if attempt < MAX_RETRIES - 1:
                    print(f"⏳ Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    return {
                        'file': track_path.name,
                        'success': False,
                        'error': error_detail,
                        'status_code': response.status_code
                    }
        
        except requests.exceptions.Timeout:
            print(f"⏱️  Request timed out (attempt {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                return {
                    'file': track_path.name,
                    'success': False,
                    'error': str(e)
                }
    
    return None


def run_test_suite(loop: bool = False):
    """Run tests on all tracks"""
    print("🚀 Type Beat Analyzer - Test Suite")
    print("=" * 60)
    
    # Check backend
    if not check_backend_health():
        print("\n❌ Backend is not running!")
        print("   Please start the backend first:")
        print("   cd backend && python -m uvicorn main:app --port 8000")
        return
    
    print("✅ Backend is running")
    
    # Find all test tracks
    if not TEST_TRACKS_DIR.exists():
        print(f"❌ Test tracks directory not found: {TEST_TRACKS_DIR}")
        return
    
    tracks = list(TEST_TRACKS_DIR.glob("*.mp3"))
    if not tracks:
        print(f"❌ No MP3 files found in {TEST_TRACKS_DIR}")
        return
    
    print(f"📁 Found {len(tracks)} test track(s)")
    
    iteration = 0
    while True:
        iteration += 1
        if loop:
            print(f"\n{'='*60}")
            print(f"🔄 Test Iteration #{iteration}")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"🧪 Running Single Test Pass")
            print(f"{'='*60}")
        
        results = []
        for track in sorted(tracks):
            result = analyze_track(track)
            if result:
                results.append(result)
            time.sleep(1)  # Small delay between tracks
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 Test Summary")
        print(f"{'='*60}")
        
        successful = sum(1 for r in results if r.get('success'))
        total = len(results)
        
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Failed: {total - successful}/{total}")
        
        if successful > 0:
            avg_matches = sum(r.get('matches', 0) for r in results if r.get('success')) / successful
            print(f"📈 Average matches per track: {avg_matches:.1f}")
        
        # Show detailed results
        print("\n📋 Detailed Results:")
        for result in results:
            status = "✅" if result.get('success') else "❌"
            matches = result.get('matches', 0)
            print(f"  {status} {result['file']}: {matches} match(es)")
            if not result.get('success'):
                print(f"     Error: {result.get('error', 'Unknown')}")
        
        if not loop:
            break
        
        print(f"\n⏳ Waiting 10 seconds before next iteration...")
        time.sleep(10)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test audio analysis with test tracks")
    parser.add_argument("--loop", action="store_true", help="Run tests in a loop")
    parser.add_argument("--backend-url", default=BACKEND_URL, help="Backend URL")
    
    args = parser.parse_args()
    BACKEND_URL = args.backend_url
    
    try:
        run_test_suite(loop=args.loop)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test suite stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
