"""
Script to download type beats from YouTube for training dataset
Uses yt-dlp to download audio from "[Artist] type beat" searches
"""

import yt_dlp
import os
from pathlib import Path
from typing import List
import argparse
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_type_beats(
    artist: str,
    output_dir: str,
    max_results: int = 50,
    duration_limit: int = 30
):
    """
    Download type beats for a specific artist from YouTube
    
    Args:
        artist: Artist name (e.g., "Drake")
        output_dir: Directory to save audio files
        max_results: Maximum number of videos to download
        duration_limit: Maximum duration in seconds (30s is enough per research)
    """
    output_path = Path(output_dir) / artist.lower().replace(" ", "_")
    output_path.mkdir(parents=True, exist_ok=True)
    
    search_query = f"{artist} type beat"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_path / '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'extractaudio': True,
        'audioformat': 'wav',
        'audioquality': '192K',
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'default_search': 'ytsearch',
        'max_downloads': max_results,
        'match_filter': lambda info: (
            None if info.get('duration', 0) > duration_limit * 2
            else None  # Download if duration is reasonable
        ),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Searching for: {search_query}")
            ydl.download([search_query])
            logger.info(f"Downloaded beats for {artist} to {output_path}")
    except Exception as e:
        logger.error(f"Error downloading for {artist}: {str(e)}")


def download_multiple_artists(
    artists: List[str],
    output_dir: str = "data/raw",
    max_per_artist: int = 50
):
    """
    Download type beats for multiple artists
    """
    for artist in artists:
        logger.info(f"Downloading beats for {artist}...")
        download_type_beats(artist, output_dir, max_results=max_per_artist)
        time.sleep(2)  # Rate limiting


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download type beats from YouTube")
    parser.add_argument("--artists", nargs="+", required=True,
                       help="List of artists to download beats for")
    parser.add_argument("--output_dir", type=str, default="data/raw",
                       help="Output directory")
    parser.add_argument("--max_per_artist", type=int, default=50,
                       help="Maximum downloads per artist")
    
    args = parser.parse_args()
    
    download_multiple_artists(
        artists=args.artists,
        output_dir=args.output_dir,
        max_per_artist=args.max_per_artist
    )
