"""
Hybrid Trainer - Uses YouTube downloads + Spotify previews
Best of both worlds: Fast YouTube downloads + Spotify when available
"""

import os
import sys
import tempfile
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import numpy as np
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
import time
import subprocess

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app.fingerprint_service import FingerprintService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridTrainer:
    """
    Hybrid trainer that uses:
    1. YouTube downloads (fast, reliable, 100% success)
    2. Spotify previews (when available, as supplement)
    """
    
    def __init__(self, spotify_client_id: Optional[str] = None,
                 spotify_client_secret: Optional[str] = None,
                 youtube_api_key: Optional[str] = None):
        """
        Initialize hybrid trainer
        
        Args:
            spotify_client_id: Spotify API client ID (optional)
            spotify_client_secret: Spotify API client secret (optional)
            youtube_api_key: YouTube Data API v3 key (optional, falls back to env var)
        """
        self.fingerprint_service = FingerprintService()
        self.training_data = []
        self.output_dir = Path("data/training_fingerprints")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize YouTube API (preferred method)
        youtube_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY")
        if youtube_key:
            try:
                from googleapiclient.discovery import build
                self.youtube = build('youtube', 'v3', developerKey=youtube_key)
                self.youtube_api_available = True
                logger.info("✅ YouTube Data API v3 initialized")
            except Exception as e:
                logger.warning(f"YouTube API initialization failed: {e}")
                self.youtube = None
                self.youtube_api_available = False
        else:
            self.youtube = None
            self.youtube_api_available = False
            logger.info("ℹ️  YouTube API not configured, will use yt-dlp scraping")
        
        # Initialize Spotify API (optional)
        if spotify_client_id and spotify_client_secret:
            try:
                client_credentials = SpotifyClientCredentials(
                    client_id=spotify_client_id,
                    client_secret=spotify_client_secret
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials)
                logger.info("✅ Spotify API initialized (optional)")
            except Exception as e:
                logger.warning(f"Spotify API not available: {e}")
                self.spotify = None
        else:
            self.spotify = None
            logger.info("ℹ️  Spotify API not configured (using YouTube only)")
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration string to seconds"""
        import re
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    
    def _search_youtube_via_api(self, artist: str, max_videos: int = 50) -> List[Dict]:
        """
        Search YouTube using Data API v3 (preferred method)
        
        Args:
            artist: Artist name
            max_videos: Maximum number of videos to return
            
        Returns:
            List of video info dictionaries
        """
        if not self.youtube_api_available:
            return []
        
        all_video_info = []
        
        # Try multiple search queries
        search_queries = [
            f"{artist} official music",
            f"{artist} songs",
            f"{artist}",
        ]
        
        for search_query in search_queries:
            try:
                # Search for videos
                search_response = self.youtube.search().list(
                    q=search_query,
                    part='id,snippet',
                    type='video',
                    order='viewCount',  # Sort by views (most popular first)
                    maxResults=min(max_videos, 50),  # API limit is 50 per request
                    videoCategoryId='10'  # Music category
                ).execute()
                
                if not search_response.get('items'):
                    logger.debug(f"No results for query: {search_query}")
                    continue
                
                # Get video IDs
                video_ids = [item['id']['videoId'] for item in search_response['items']]
                
                # Get detailed video statistics
                videos_response = self.youtube.videos().list(
                    part='statistics,snippet,contentDetails',
                    id=','.join(video_ids)
                ).execute()
                
                # Process results
                for video in videos_response.get('items', []):
                    stats = video.get('statistics', {})
                    snippet = video.get('snippet', {})
                    
                    video_data = {
                        'id': video['id'],
                        'title': snippet.get('title', ''),
                        'view_count': int(stats.get('viewCount', 0)),
                        'like_count': int(stats.get('likeCount', 0)),
                        'comment_count': int(stats.get('commentCount', 0)),
                        'uploader': snippet.get('channelTitle', ''),
                        'url': f"https://www.youtube.com/watch?v={video['id']}",
                        'duration': self._parse_duration(video.get('contentDetails', {}).get('duration', 'PT0S')),
                    }
                    
                    # Avoid duplicates
                    if not any(v.get('id') == video_data.get('id') for v in all_video_info):
                        all_video_info.append(video_data)
                
                # If we got enough results, break
                if len(all_video_info) >= max_videos:
                    break
                    
            except Exception as e:
                logger.warning(f"Error searching YouTube API with query '{search_query}': {e}")
                continue
        
        logger.info(f"📊 YouTube API found {len(all_video_info)} videos for {artist}")
        return all_video_info[:max_videos]
    
    def _search_youtube_via_scraping(self, artist: str, max_videos: int = 50) -> List[Dict]:
        """
        Fallback: Search YouTube using yt-dlp scraping

        Args:
            artist: Artist name
            max_videos: Maximum number of videos to return

        Returns:
            List of video info dictionaries
        """
        try:
            import yt_dlp

            # Multiple search strategies for better results
            search_queries = [
                f"ytsearch{max_videos}:{artist} official music video",
                f"ytsearch{max_videos}:{artist} official",
                f"ytsearch{max_videos}:{artist} music",
                f"ytsearch{max_videos}:{artist}",
            ]

            all_video_info = []

            # Use extract_flat=True for faster, more reliable searches
            info_opts = {
                'quiet': False,  # Enable for debugging
                'no_warnings': False,
                'extract_flat': True,  # Don't extract full info, just metadata
                'ignoreerrors': True,  # Continue on errors
                'nocheckcertificate': True,  # Bypass SSL issues
            }

            for search_query in search_queries:
                try:
                    logger.info(f"🔍 Trying search query: {search_query}")
                    with yt_dlp.YoutubeDL(info_opts) as ydl:
                        info = ydl.extract_info(search_query, download=False)

                        if not info:
                            logger.warning(f"❌ No info returned for query: {search_query}")
                            continue

                        if 'entries' not in info:
                            logger.warning(f"❌ No 'entries' in info for query: {search_query}")
                            # Check if it's a direct video result
                            if 'id' in info:
                                logger.info(f"✅ Found direct video result")
                                all_video_info.append({
                                    'id': info.get('id'),
                                    'title': info.get('title', ''),
                                    'view_count': info.get('view_count', 0),
                                    'url': info.get('url') or f"https://www.youtube.com/watch?v={info.get('id')}",
                                })
                            continue

                        entries = info.get('entries', [])
                        logger.info(f"📋 Found {len(entries)} entries for query: {search_query}")

                        for entry in entries:
                            if entry and isinstance(entry, dict) and entry.get('id'):
                                video_data = {
                                    'id': entry.get('id'),
                                    'title': entry.get('title', 'Unknown'),
                                    'view_count': entry.get('view_count', 0),
                                    'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
                                    'duration': entry.get('duration', 0),
                                }

                                # Avoid duplicates
                                if not any(v.get('id') == video_data.get('id') for v in all_video_info):
                                    all_video_info.append(video_data)

                        logger.info(f"✅ Collected {len(all_video_info)} unique videos so far")

                except Exception as e:
                    logger.warning(f"❌ Error scraping YouTube with query '{search_query}': {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    continue

                # If we got enough results, break
                if len(all_video_info) >= max_videos:
                    logger.info(f"✅ Found {len(all_video_info)} videos, stopping search")
                    break

            logger.info(f"📊 yt-dlp scraping found {len(all_video_info)} videos for {artist}")
            return all_video_info[:max_videos]
            
        except ImportError:
            logger.error("yt-dlp not installed. Install with: pip install yt-dlp")
            return []
        except Exception as e:
            logger.error(f"Error scraping YouTube: {e}")
            return []
    
    def download_from_youtube(self, artist: str, max_videos: int = 50) -> List[str]:
        """
        Download official songs from artist on YouTube
        Uses YouTube API first, falls back to yt-dlp scraping
        
        Args:
            artist: Artist name
            max_videos: Max videos to download
            
        Returns:
            List of downloaded file paths, sorted by performance
        """
        logger.info(f"📥 Searching for top-performing '{artist}' songs on YouTube...")
        
        temp_dir = Path(f"/tmp/typebeat_{artist}_{int(time.time())}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Search for videos (API first, then scraping fallback)
        all_video_info = []
        
        if self.youtube_api_available:
            logger.info("🔍 Using YouTube Data API v3 for search...")
            all_video_info = self._search_youtube_via_api(artist, max_videos)
        
        # Fallback to scraping if API failed or not available
        if not all_video_info:
            logger.info("🔍 Falling back to yt-dlp scraping...")
            all_video_info = self._search_youtube_via_scraping(artist, max_videos)
        
        if not all_video_info:
            logger.warning(f"❌ No videos found for {artist} via any method")
            return []
        
        # Step 2: Filter and sort videos
        def is_likely_official(video):
            uploader_lower = video.get('uploader', '').lower()
            title_lower = video.get('title', '').lower()
            artist_lower = artist.lower()
            
            official_indicators = [
                'vevo' in uploader_lower,
                'official' in uploader_lower,
                artist_lower in uploader_lower,
                'official' in title_lower,
            ]
            
            non_official = [
                'cover' in title_lower,
                'remix' in title_lower,
                'reaction' in title_lower,
                'live' in title_lower and 'concert' not in title_lower,
            ]
            
            return any(official_indicators) and not any(non_official)
        
        def engagement_score(video):
            views = video.get('view_count', 0)
            comments = video.get('comment_count', 0)
            likes = video.get('like_count', 0)
            return views + (comments * 100) + (likes * 10)
        
        # Filter out obvious non-music content
        filtered_videos = []
        for video in all_video_info:
            title_lower = video.get('title', '').lower()
            skip_keywords = ['cover', 'remix', 'reaction', 'live performance']
            if not any(keyword in title_lower for keyword in skip_keywords):
                filtered_videos.append(video)
        
        # If filtering removed too much, use all videos
        if len(filtered_videos) < max_videos // 2:
            filtered_videos = all_video_info
        
        # Sort by official status and engagement
        filtered_videos.sort(
            key=lambda x: (
                not is_likely_official(x),
                -engagement_score(x)
            )
        )
        
        top_videos = filtered_videos[:max_videos]
        logger.info(f"📊 Selected {len(top_videos)} top videos (sorted by performance)")
        
        # Step 3: Download videos using yt-dlp
        try:
            import yt_dlp
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'extractaudio': True,
                'audioformat': 'wav',
                'quiet': False,
                'no_warnings': False,
                # Add timeout configurations to prevent deployment hangs
                'socket_timeout': 60,  # 60 seconds
                'retries': 3,  # Retry failed downloads
                'fileaccess_retries': 3,
                # Bypass YouTube bot detection
                'nocheckcertificate': True,  # Bypass SSL verification issues
                'geo_bypass': True,  # Bypass geographic restrictions
                'no_playlist': True,  # Download single video only
                # DON'T ignore errors - we want exceptions to trigger pytube fallback
                # Use a user agent to appear more like a browser
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            }
            
            downloaded_files = []
            for i, video in enumerate(top_videos, 1):
                try:
                    logger.info(f"[{i}/{len(top_videos)}] Downloading: {video['title'][:50]}... ({video.get('view_count', 0):,} views)")

                    # Try yt-dlp first with bypass options
                    try:
                        logger.info(f"   🔄 Attempting yt-dlp download...")
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([video['url']])

                        # Find the downloaded file
                        audio_files = list(temp_dir.glob("*.wav"))
                        logger.info(f"   🔍 Found {len(audio_files)} .wav files in temp_dir")
                        if audio_files:
                            latest_file = max(audio_files, key=lambda p: p.stat().st_mtime)
                            logger.info(f"   📁 Latest file: {latest_file}")
                            if str(latest_file) not in downloaded_files:
                                downloaded_files.append(str(latest_file))
                                logger.info(f"   ✅ Downloaded successfully via yt-dlp")
                                continue
                        else:
                            logger.warning(f"   ⚠️  No .wav files found after yt-dlp download")
                    except Exception as yt_dlp_error:
                        logger.warning(f"   ⚠️  yt-dlp failed: {str(yt_dlp_error)[:200]}")
                        logger.info(f"   🔄 Trying pytube as fallback...")

                        # Fallback to pytube
                        try:
                            logger.info(f"   🔄 Importing pytube...")
                            from pytube import YouTube
                            logger.info(f"   ✅ pytube imported successfully")

                            # Use pytube to download
                            logger.info(f"   🔄 Initializing YouTube object...")
                            yt = YouTube(video['url'])
                            logger.info(f"   🔄 Getting audio stream...")
                            audio_stream = yt.streams.get_audio_only()
                            logger.info(f"   ✅ Got audio stream: {audio_stream}")

                            if audio_stream:
                                # Download to temp file
                                temp_filename = temp_dir / f"{video['id']}.wav"
                                audio_stream.download(output_path=str(temp_filename),
                                                       filename=f"{video['id']}.wav")

                                if temp_filename.exists() and str(temp_filename) not in downloaded_files:
                                    downloaded_files.append(str(temp_filename))
                                    logger.info(f"   ✅ Downloaded successfully via pytube")
                                    continue
                        except ImportError:
                            logger.error("   ❌ pytube not installed. Add pytube==15.0.6 to requirements.txt")
                            continue
                        except Exception as pytube_error:
                            logger.warning(f"   ❌ pytube also failed: {str(pytube_error)[:100]}")
                            continue

                except Exception as e:
                    logger.warning(f"Error downloading {video.get('title', 'unknown')}: {e}")
                    continue
            
            logger.info(f"✅ Downloaded {len(downloaded_files)} top-performing videos from YouTube")
            return downloaded_files
            
        except ImportError:
            logger.error("yt-dlp not installed. Install with: pip install yt-dlp")
            return []
        except Exception as e:
            logger.error(f"Error downloading from YouTube: {e}")
            return []
    
    def get_spotify_previews(self, artist: str, max_tracks: int = 50) -> List[Dict]:
        """
        Get Spotify previews (when available)
        
        Args:
            artist: Artist name
            max_tracks: Max tracks to search
            
        Returns:
            List of track info with preview URLs
        """
        if not self.spotify:
            return []
        
        try:
            max_per_request = 10  # Development Mode limit
            all_tracks = []
            
            for offset in range(0, min(max_tracks, 100), max_per_request):
                results = self.spotify.search(
                    q=f'artist:{artist}',
                    type='track',
                    limit=min(max_per_request, max_tracks - offset),
                    offset=offset
                )
                all_tracks.extend(results['tracks']['items'])
            
            tracks_with_previews = []
            for track in all_tracks:
                if track.get('preview_url'):
                    tracks_with_previews.append({
                        'id': track['id'],
                        'name': track['name'],
                        'preview_url': track['preview_url'],
                        'artist': artist,
                        'duration_ms': track.get('duration_ms', 0)
                    })
            
            logger.info(f"✅ Found {len(tracks_with_previews)} Spotify previews for {artist}")
            return tracks_with_previews
            
        except Exception as e:
            logger.error(f"Error fetching Spotify tracks: {e}")
            return []
    
    def fingerprint_audio_file(self, audio_path: str, artist: str, 
                             track_name: str = "") -> Optional[np.ndarray]:
        """
        Generate fingerprint from audio file
        
        Args:
            audio_path: Path to audio file
            artist: Artist name
            track_name: Track name (for logging)
            
        Returns:
            Fingerprint embedding or None
        """
        try:
            fingerprint = self.fingerprint_service._generate_fingerprint(audio_path, duration=None)
            logger.debug(f"Generated fingerprint for {track_name}: {fingerprint.shape}")
            return fingerprint
        except Exception as e:
            logger.error(f"Error generating fingerprint: {e}")
            return None
    
    def fingerprint_spotify_preview(self, preview_url: str, artist: str,
                                   track_name: str = "") -> Optional[np.ndarray]:
        """
        Download Spotify preview and generate fingerprint
        
        Args:
            preview_url: URL to 30-second preview
            artist: Artist name
            track_name: Track name
            
        Returns:
            Fingerprint embedding or None
        """
        temp_file = None
        try:
            response = requests.get(preview_url, timeout=10)
            response.raise_for_status()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.write(response.content)
            temp_file.close()
            
            fingerprint = self.fingerprint_service._generate_fingerprint(temp_file.name, duration=None)
            return fingerprint
            
        except Exception as e:
            logger.error(f"Error processing Spotify preview: {e}")
            return None
        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
    
    def train_artist_hybrid(self, artist_name: str, max_items: int = 50) -> int:
        """
        Train on artist using both YouTube and Spotify
        
        Args:
            artist_name: Artist to train on
            max_items: Max items per source
            
        Returns:
            Number of fingerprints generated
        """
        logger.info(f"🎵 Training on {artist_name} (hybrid approach)...")
        
        fingerprints_generated = 0
        
        # Method 1: YouTube (fast, reliable, top-performing official songs)
        logger.info(f"📥 Method 1: Downloading top-performing official songs from YouTube...")
        youtube_files = self.download_from_youtube(artist_name, max_videos=max_items)
        
        for i, audio_file in enumerate(youtube_files, 1):
            logger.info(f"[YouTube {i}/{len(youtube_files)}] Processing: {Path(audio_file).stem}")
            
            fingerprint = self.fingerprint_audio_file(audio_file, artist_name, Path(audio_file).stem)
            
            if fingerprint is not None:
                self.training_data.append({
                    'fingerprint': fingerprint.tolist(),
                    'artist': artist_name,
                    'track_name': Path(audio_file).stem,
                    'source': 'youtube_download',
                    'timestamp': time.time()
                })
                fingerprints_generated += 1
            
            # Delete audio file immediately
            try:
                os.unlink(audio_file)
            except:
                pass
        
        # Method 2: Spotify previews (supplement, when available)
        if self.spotify:
            logger.info(f"🎵 Method 2: Checking Spotify previews...")
            spotify_tracks = self.get_spotify_previews(artist_name, max_tracks=max_items)
            
            for i, track in enumerate(spotify_tracks, 1):
                logger.info(f"[Spotify {i}/{len(spotify_tracks)}] Processing: {track['name']}")
                
                fingerprint = self.fingerprint_spotify_preview(
                    track['preview_url'],
                    artist_name,
                    track['name']
                )
                
                if fingerprint is not None:
                    self.training_data.append({
                        'fingerprint': fingerprint.tolist(),
                        'artist': artist_name,
                        'track_name': track['name'],
                        'track_id': track['id'],
                        'source': 'spotify_streaming',
                        'timestamp': time.time()
                    })
                    fingerprints_generated += 1
                    time.sleep(0.5)  # Rate limiting
        
        logger.info(f"✅ Generated {fingerprints_generated} fingerprints for {artist_name}")
        return fingerprints_generated
    
    def train_multiple_artists(self, artists: List[str], max_items_per_artist: int = 50):
        """
        Train on multiple artists using hybrid approach
        
        Args:
            artists: List of artist names
            max_items_per_artist: Max items per artist per source
        """
        logger.info(f"🚀 Starting hybrid training for {len(artists)} artists...")
        
        total_fingerprints = 0
        
        for artist in artists:
            count = self.train_artist_hybrid(artist, max_items_per_artist)
            total_fingerprints += count
            
            # Save after each artist (incremental)
            self.save_training_data()
            
            time.sleep(2)  # Rate limiting between artists
        
        logger.info(f"✅ Training complete! Generated {total_fingerprints} total fingerprints")
        return total_fingerprints
    
    def save_training_data(self, filename: Optional[str] = None):
        """Save training data"""
        if not filename:
            timestamp = int(time.time())
            filename = f"training_fingerprints_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(self.training_data, f, indent=2)
        
        logger.info(f"💾 Saved {len(self.training_data)} fingerprints to {output_path}")


def main():
    """Main function"""
    import argparse
    from dotenv import load_dotenv
    
    env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
    load_dotenv(env_path)
    
    parser = argparse.ArgumentParser(description="Hybrid trainer (YouTube + Spotify)")
    parser.add_argument("--artists", nargs="+", required=True,
                       help="List of artists to train on")
    parser.add_argument("--items-per-artist", type=int, default=50,
                       help="Max items per artist per source")
    parser.add_argument("--spotify-id", type=str, default=None,
                       help="Spotify Client ID (optional)")
    parser.add_argument("--spotify-secret", type=str, default=None,
                       help="Spotify Client Secret (optional)")
    
    args = parser.parse_args()
    
    spotify_id = args.spotify_id or os.getenv("SPOTIFY_CLIENT_ID")
    spotify_secret = args.spotify_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
    
    trainer = HybridTrainer(spotify_id, spotify_secret)
    trainer.train_multiple_artists(args.artists, args.items_per_artist)
    trainer.save_training_data("final_training_data.json")
    
    logger.info("✅ All done! Fingerprints saved (no audio files stored)")


if __name__ == "__main__":
    main()
