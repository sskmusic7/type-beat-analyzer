"""
Automated streaming trainer - streams from APIs, generates fingerprints, trains model
Legal: Only stores fingerprints (not audio), deletes audio immediately
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

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app.fingerprint_service import FingerprintService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamingTrainer:
    """
    Automated trainer that streams from APIs, generates fingerprints,
    and stores only fingerprints (not audio files)
    """
    
    def __init__(self, spotify_client_id: Optional[str] = None,
                 spotify_client_secret: Optional[str] = None):
        """
        Initialize streaming trainer
        
        Args:
            spotify_client_id: Spotify API client ID
            spotify_client_secret: Spotify API client secret
        """
        self.fingerprint_service = FingerprintService()
        self.training_data = []
        self.output_dir = Path("data/training_fingerprints")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Spotify API
        if spotify_client_id and spotify_client_secret:
            try:
                client_credentials = SpotifyClientCredentials(
                    client_id=spotify_client_id,
                    client_secret=spotify_client_secret
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials)
                logger.info("✅ Spotify API initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify API: {e}")
                self.spotify = None
        else:
            self.spotify = None
            logger.warning("Spotify credentials not provided")
    
    def get_artist_tracks(self, artist_name: str, limit: int = 50) -> List[Dict]:
        """
        Get track previews for an artist from Spotify
        
        Args:
            artist_name: Name of artist
            limit: Max number of tracks to get
            
        Returns:
            List of track info with preview URLs
        """
        if not self.spotify:
            logger.error("Spotify API not initialized")
            return []
        
        try:
            # Search for artist (Development Mode limit is 10 per request)
            # If limit > 10, we need multiple requests
            max_per_request = 10  # Development Mode restriction
            all_tracks = []
            
            for offset in range(0, min(limit, 100), max_per_request):  # Max 100 tracks total
                results = self.spotify.search(
                    q=f'artist:{artist_name}', 
                    type='track', 
                    limit=min(max_per_request, limit - offset),
                    offset=offset
                )
                all_tracks.extend(results['tracks']['items'])
            
            results = {'tracks': {'items': all_tracks}}
            
            tracks = []
            for track in results['tracks']['items']:
                if track.get('preview_url'):  # Has 30s preview
                    tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'preview_url': track['preview_url'],
                        'artist': artist_name,
                        'duration_ms': track.get('duration_ms', 0)
                    })
            
            logger.info(f"Found {len(tracks)} tracks with previews for {artist_name}")
            return tracks
            
        except Exception as e:
            logger.error(f"Error fetching tracks for {artist_name}: {e}")
            return []
    
    def stream_and_fingerprint(self, preview_url: str, artist: str, 
                              track_name: str = "") -> Optional[np.ndarray]:
        """
        Stream preview, generate fingerprint, delete audio
        
        Args:
            preview_url: URL to 30-second preview
            artist: Artist name
            track_name: Track name (for logging)
            
        Returns:
            Fingerprint embedding (128-dim) or None if failed
        """
        temp_file = None
        try:
            # Download preview (30 seconds, legal)
            logger.debug(f"Downloading preview: {track_name}")
            response = requests.get(preview_url, timeout=10)
            response.raise_for_status()
            
            # Save temporarily
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.write(response.content)
            temp_file.close()
            
            # Generate fingerprint (use full duration for training)
            fingerprint = self.fingerprint_service._generate_fingerprint(temp_file.name, duration=None)
            
            logger.debug(f"Generated fingerprint for {track_name}: {fingerprint.shape}")
            return fingerprint
            
        except Exception as e:
            logger.error(f"Error processing {track_name}: {e}")
            return None
            
        finally:
            # Always delete audio immediately
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
    
    def train_artist_from_spotify(self, artist_name: str, max_tracks: int = 50) -> int:
        """
        Automatically train on an artist by streaming from Spotify
        
        Args:
            artist_name: Artist to train on
            max_tracks: Maximum tracks to process
            
        Returns:
            Number of fingerprints generated
        """
        logger.info(f"🎵 Training on {artist_name} from Spotify...")
        
        # Get tracks
        tracks = self.get_artist_tracks(artist_name, limit=max_tracks)
        
        if not tracks:
            logger.warning(f"No tracks found for {artist_name}")
            return 0
        
        fingerprints_generated = 0
        
        for i, track in enumerate(tracks, 1):
            logger.info(f"[{i}/{len(tracks)}] Processing: {track['name']}")
            
            # Stream and fingerprint
            fingerprint = self.stream_and_fingerprint(
                track['preview_url'],
                artist_name,
                track['name']
            )
            
            if fingerprint is not None:
                # Store fingerprint (not audio!)
                self.training_data.append({
                    'fingerprint': fingerprint.tolist(),  # Convert to list for JSON
                    'artist': artist_name,
                    'track_name': track['name'],
                    'track_id': track['id'],
                    'source': 'spotify_streaming',
                    'timestamp': time.time()
                })
                fingerprints_generated += 1
                
                # Rate limiting (be nice to APIs)
                time.sleep(0.5)
        
        logger.info(f"✅ Generated {fingerprints_generated} fingerprints for {artist_name}")
        return fingerprints_generated
    
    def train_multiple_artists(self, artists: List[str], max_tracks_per_artist: int = 50):
        """
        Train on multiple artists automatically
        
        Args:
            artists: List of artist names
            max_tracks_per_artist: Max tracks per artist
        """
        logger.info(f"🚀 Starting automated training for {len(artists)} artists...")
        
        total_fingerprints = 0
        
        for artist in artists:
            count = self.train_artist_from_spotify(artist, max_tracks_per_artist)
            total_fingerprints += count
            
            # Save after each artist (incremental)
            self.save_training_data()
            
            # Rate limiting between artists
            time.sleep(2)
        
        logger.info(f"✅ Training complete! Generated {total_fingerprints} total fingerprints")
        return total_fingerprints
    
    def save_training_data(self, filename: Optional[str] = None):
        """
        Save training data (fingerprints only, no audio!)
        
        Args:
            filename: Optional filename, defaults to timestamped file
        """
        if not filename:
            timestamp = int(time.time())
            filename = f"training_fingerprints_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(self.training_data, f, indent=2)
        
        logger.info(f"💾 Saved {len(self.training_data)} fingerprints to {output_path}")
    
    def load_training_data(self, filename: str):
        """Load previously saved training data"""
        input_path = self.output_dir / filename
        
        if not input_path.exists():
            logger.error(f"File not found: {input_path}")
            return
        
        with open(input_path, 'r') as f:
            self.training_data = json.load(f)
        
        logger.info(f"📂 Loaded {len(self.training_data)} fingerprints from {input_path}")
    
    def export_for_model_training(self) -> Dict:
        """
        Export fingerprints in format for model training
        
        Returns:
            Dict with fingerprints and labels ready for PyTorch
        """
        if not self.training_data:
            logger.warning("No training data available")
            return {}
        
        # Group by artist
        artist_fingerprints = {}
        for item in self.training_data:
            artist = item['artist']
            if artist not in artist_fingerprints:
                artist_fingerprints[artist] = []
            artist_fingerprints[artist].append(np.array(item['fingerprint']))
        
        # Convert to format for training
        all_fingerprints = []
        all_labels = []
        artist_to_idx = {artist: idx for idx, artist in enumerate(artist_fingerprints.keys())}
        
        for artist, fingerprints in artist_fingerprints.items():
            for fingerprint in fingerprints:
                all_fingerprints.append(fingerprint)
                all_labels.append(artist_to_idx[artist])
        
        return {
            'fingerprints': np.array(all_fingerprints),
            'labels': np.array(all_labels),
            'artist_list': list(artist_fingerprints.keys()),
            'artist_to_idx': artist_to_idx
        }


def main():
    """Main function for CLI usage"""
    import argparse
    from dotenv import load_dotenv
    
    # Load environment
    env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
    load_dotenv(env_path)
    
    parser = argparse.ArgumentParser(description="Automated streaming trainer")
    parser.add_argument("--artists", nargs="+", required=True,
                       help="List of artists to train on")
    parser.add_argument("--tracks-per-artist", type=int, default=50,
                       help="Max tracks per artist")
    parser.add_argument("--spotify-id", type=str, default=None,
                       help="Spotify Client ID (or set SPOTIFY_CLIENT_ID env var)")
    parser.add_argument("--spotify-secret", type=str, default=None,
                       help="Spotify Client Secret (or set SPOTIFY_CLIENT_SECRET env var)")
    
    args = parser.parse_args()
    
    # Get Spotify credentials
    spotify_id = args.spotify_id or os.getenv("SPOTIFY_CLIENT_ID")
    spotify_secret = args.spotify_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not spotify_id or not spotify_secret:
        logger.error("Spotify credentials required!")
        logger.error("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in backend/.env")
        logger.error("Or get them from: https://developer.spotify.com/dashboard")
        sys.exit(1)
    
    # Initialize trainer
    trainer = StreamingTrainer(spotify_id, spotify_secret)
    
    # Train on artists
    trainer.train_multiple_artists(args.artists, args.tracks_per_artist)
    
    # Save final data
    trainer.save_training_data("final_training_data.json")
    
    logger.info("✅ All done! Fingerprints saved (no audio files stored)")


if __name__ == "__main__":
    main()
