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
                 upload_to_cloud: bool = True):
        """
        Initialize hybrid trainer

        Args:
            spotify_client_id: Spotify API client ID (optional)
            spotify_client_secret: Spotify API client secret (optional)
            upload_to_cloud: Upload results to Cloud Storage (default True)
        """
        self.fingerprint_service = FingerprintService()
        self.training_data = []
        self.output_dir = Path("data/training_fingerprints")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.upload_to_cloud = upload_to_cloud

        # Training status for webhook server
        self.is_running = False
        self.current_status = {
            "status": "idle",
            "progress": 0,
            "message": "",
            "current_artist": None,
            "total_artists": 0,
            "completed_artists": 0
        }

        # Initialize Cloud Storage uploader
        if self.upload_to_cloud:
            try:
                from app.fingerprint_service_cloud_storage import CloudStorageUploader
                self.cloud_uploader = CloudStorageUploader()
                logger.info("✅ Cloud Storage uploader initialized")
            except Exception as e:
                logger.warning(f"⚠️  Cloud Storage uploader not available: {e}")
                self.cloud_uploader = None
        else:
            self.cloud_uploader = None
        
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
    
    def download_from_youtube(self, artist: str, max_videos: int = 50) -> List[str]:
        """
        Download official songs from artist on YouTube
        Prioritizes top-performing videos (by views) and official channels
        
        Args:
            artist: Artist name
            max_videos: Max videos to download
            
        Returns:
            List of downloaded file paths, sorted by performance
        """
        logger.info(f"📥 Searching for top-performing '{artist}' songs on YouTube...")
        
        temp_dir = Path(f"/tmp/typebeat_{artist}_{int(time.time())}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            import yt_dlp
            
            # Search for official artist songs (not type beats)
            # Prioritize: official music, top views, official channels
            search_queries = [
                f"ytsearch{max_videos}:{artist} official music",  # Official music first
                f"ytsearch{max_videos}:{artist} songs",  # General songs
                f"ytsearch{max_videos}:{artist} type beat",  # Type beats as fallback
            ]
            
            all_video_info = []
            
            # First, get video info without downloading (to sort by views + comments)
            info_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
            }
            
            for search_query in search_queries[:1]:  # Start with official music only
                try:
                    with yt_dlp.YoutubeDL(info_opts) as ydl:
                        # Extract info for all videos
                        info = ydl.extract_info(search_query, download=False)
                        if 'entries' in info:
                            for entry in info['entries']:
                                if entry:
                                    # Get comment count if available
                                    comment_count = entry.get('comment_count', 0)
                                    
                                    all_video_info.append({
                                        'id': entry.get('id'),
                                        'title': entry.get('title', ''),
                                        'view_count': entry.get('view_count', 0),
                                        'comment_count': comment_count,
                                        'like_count': entry.get('like_count', 0),
                                        'uploader': entry.get('uploader', ''),
                                        'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
                                        'duration': entry.get('duration', 0),
                                    })
                except Exception as e:
                    logger.warning(f"Error getting info for {search_query}: {e}")
                    continue
            
            # Filter and sort by views (top performing)
            # Prefer official channels (artist name in channel or "VEVO", "Official")
            def is_likely_official(video):
                uploader_lower = video.get('uploader', '').lower()
                title_lower = video.get('title', '').lower()
                artist_lower = artist.lower()
                
                # Check for official indicators
                official_indicators = [
                    'vevo' in uploader_lower,
                    'official' in uploader_lower,
                    artist_lower in uploader_lower,
                    'official' in title_lower,
                ]
                
                # Check for non-official indicators (covers, remixes)
                non_official = [
                    'cover' in title_lower,
                    'remix' in title_lower,
                    'reaction' in title_lower,
                    'live' in title_lower and 'concert' not in title_lower,
                ]
                
                return any(official_indicators) and not any(non_official)
            
            # Sort by: official first, then by engagement (views + comments)
            # Engagement score = views + (comments * 100) to prioritize videos with high engagement
            def engagement_score(video):
                views = video.get('view_count', 0)
                comments = video.get('comment_count', 0)
                likes = video.get('like_count', 0)
                # Weight: views are primary, comments show engagement, likes are bonus
                return views + (comments * 100) + (likes * 10)
            
            all_video_info.sort(
                key=lambda x: (
                    not is_likely_official(x),  # Official videos first
                    -engagement_score(x)  # Then by engagement score (descending)
                )
            )
            
            # Take top videos
            top_videos = all_video_info[:max_videos]
            logger.info(f"📊 Found {len(top_videos)} top videos (sorted by performance)")
            
            if not top_videos:
                logger.warning(f"No videos found for {artist}")
                return []
            
            # Download top videos
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
            }
            
            downloaded_files = []
            for i, video in enumerate(top_videos, 1):
                try:
                    logger.info(f"[{i}/{len(top_videos)}] Downloading: {video['title'][:50]}... ({video.get('view_count', 0):,} views)")
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video['url']])
                    
                    # Find the downloaded file
                    audio_files = list(temp_dir.glob("*.wav"))
                    if audio_files:
                        # Get the most recently created file
                        latest_file = max(audio_files, key=lambda p: p.stat().st_mtime)
                        if str(latest_file) not in downloaded_files:
                            downloaded_files.append(str(latest_file))
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

        # Upload to Cloud Storage if enabled
        if self.upload_to_cloud and self.cloud_uploader:
            try:
                # Prepare fingerprint data for upload
                upload_data = []
                for i, item in enumerate(self.training_data):
                    upload_data.append({
                        'id': i,
                        'embedding': item['fingerprint'],
                        'artist': item['artist'],
                        'title': item['track_name'],
                        'source': item['source']
                    })

                # Upload to Cloud Storage
                success = self.cloud_uploader.upload_training_results(
                    fingerprint_data=upload_data,
                    metadata_path=output_path
                )

                if success:
                    logger.info("✅ Uploaded training results to Cloud Storage")
                else:
                    logger.warning("⚠️  Failed to upload to Cloud Storage")

            except Exception as e:
                logger.error(f"❌ Error uploading to Cloud Storage: {e}")

    def get_status(self) -> Dict:
        """Get current training status"""
        return self.current_status.copy()

    def update_status(self, status: str, progress: int = None, message: str = None):
        """Update training status"""
        self.current_status["status"] = status
        if progress is not None:
            self.current_status["progress"] = progress
        if message is not None:
            self.current_status["message"] = message

    def stop_training(self):
        """Stop training"""
        self.is_running = False
        self.update_status("stopped", message="Training stopped by user")

    async def train_from_youtube(
        self,
        artists: List[str],
        max_per_artist: int = 5,
        clear_existing: bool = False
    ) -> Dict:
        """
        Train on artists from YouTube (async for webhook server)

        Args:
            artists: List of artist names
            max_per_artist: Maximum tracks per artist
            clear_existing: Clear existing fingerprints

        Returns:
            Training results dictionary
        """
        try:
            self.is_running = True
            self.current_status["total_artists"] = len(artists)
            self.current_status["completed_artists"] = 0

            if clear_existing:
                logger.info("🗑️  Clearing existing fingerprints...")
                self.training_data = []
                self.update_status("clearing", message="Clearing existing fingerprints")

            total_fingerprints = 0

            for i, artist in enumerate(artists):
                if not self.is_running:
                    logger.info("⚠️  Training stopped")
                    break

                self.current_status["current_artist"] = artist
                progress = int((i / len(artists)) * 100)
                self.update_status(
                    "training",
                    progress=progress,
                    message=f"Training on {artist} ({i+1}/{len(artists)})"
                )

                logger.info(f"🎵 Training on {artist} ({i+1}/{len(artists)})...")

                # Train on this artist
                count = self.train_artist_hybrid(artist, max_per_artist)
                total_fingerprints += count

                self.current_status["completed_artists"] = i + 1

                # Save after each artist
                self.save_training_data()

            # Final status update
            self.is_running = False
            self.update_status(
                "completed",
                progress=100,
                message=f"Training complete! Generated {total_fingerprints} fingerprints"
            )

            logger.info(f"✅ Training complete! Generated {total_fingerprints} total fingerprints")

            return {
                "success": True,
                "total_fingerprints": total_fingerprints,
                "artists_trained": self.current_status["completed_artists"],
                "message": f"Generated {total_fingerprints} fingerprints"
            }

        except Exception as e:
            self.is_running = False
            self.update_status("error", message=f"Error: {str(e)}")
            logger.error(f"❌ Training failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Training failed: {str(e)}"
            }


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
