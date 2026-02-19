"""
Discover Trending Type Beat Artists
Analyzes YouTube search results to find top artists people are searching for type beats
"""

import os
import sys
import json
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
from pathlib import Path
import time
import logging
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendingArtistDiscoverer:
    """
    Discovers trending type beat artists by analyzing YouTube search results
    """
    
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.artist_counts = Counter()
        self.video_data = []
        
    def extract_artist_from_title(self, title: str) -> List[str]:
        """
        Extract artist names from video titles like "Artist Name Type Beat"
        
        Common patterns:
        - "Drake Type Beat"
        - "Travis Scott Type Beat"
        - "Artist Name - Type Beat"
        - "Type Beat | Artist Name"
        """
        artists = []
        
        # Clean HTML entities
        title = title.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
        title_lower = title.lower()
        
        # Skip if title is too generic or not a type beat
        generic_terms = ['radio', 'mix', 'hour', 'playlist', 'stream', 'live stream', '24/7']
        if any(term in title_lower for term in generic_terms):
            return []
        
        # Pattern 1: "Artist Name Type Beat" or "Artist Name - Type Beat"
        pattern1 = re.compile(r'^([^|\[\]()]+?)\s*(?:-|\s+)?type\s+beat', re.IGNORECASE)
        match1 = pattern1.match(title)
        if match1:
            artist = match1.group(1).strip()
            if self._is_valid_artist(artist):
                artists.append(self._normalize_artist(artist))
        
        # Pattern 2: "Type Beat | Artist Name"
        pattern2 = re.compile(r'type\s+beat\s*\|\s*([^|\[\]()]+)', re.IGNORECASE)
        match2 = pattern2.search(title)
        if match2:
            artist = match2.group(1).strip()
            if self._is_valid_artist(artist):
                artists.append(self._normalize_artist(artist))
        
        # Pattern 3: "[free] Artist Name Type Beat" or "(free) Artist Name"
        pattern3 = re.compile(r'[\[\(]?free[\]\)]?\s*([^|\[\]()]+?)\s*(?:type\s+beat|sample)', re.IGNORECASE)
        match3 = pattern3.search(title)
        if match3:
            artist = match3.group(1).strip()
            if self._is_valid_artist(artist):
                artists.append(self._normalize_artist(artist))
        
        # Pattern 4: Split by common separators and check each part
        parts = re.split(r'[|\-–—]', title)
        for part in parts:
            part = part.strip()
            # Look for "Artist X Artist" or "Artist Type Beat"
            if 'type beat' in part.lower() or 'x' in part.lower():
                # Extract before "type beat" or before "X"
                artist_part = re.split(r'\s+(?:type\s+beat|x)\s+', part, flags=re.IGNORECASE)[0].strip()
                if self._is_valid_artist(artist_part):
                    artists.append(self._normalize_artist(artist_part))
        
        return list(set(artists))  # Remove duplicates
    
    def _is_valid_artist(self, name: str) -> bool:
        """Check if a name looks like a valid artist name"""
        if not name or len(name) < 2:
            return False
        
        name_lower = name.lower().strip()
        
        # Skip generic terms
        generic_terms = [
            'type', 'beat', 'free', 'download', 'instrumental', 'prod', 'by',
            'trap', 'rap', 'hip hop', 'boom bap', 'freestyle', 'dark', 'hard',
            'melodic', 'sad', 'diss', 'radio', 'mix', 'hour', 'playlist',
            'sample', 'old school', 'new jazz', 'uk drill', 'detroit',
            'bouncy', 'sold', 'for profit', 'free use', 'uso libre',
            'anabolic', 'beatz', 'chill', 'lo-fi', 'lofi', 'synthwave',
            'year', 'track', 'beats', 'instrumental'
        ]
        
        if any(term in name_lower for term in generic_terms):
            return False
        
        # Skip if contains special formatting
        if any(char in name for char in ['[', ']', '(', ')', '#', '<', '>', '&']):
            return False
        
        # Skip if looks like a description
        if name_lower.startswith('[') or name_lower.startswith('('):
            return False
        
        # Must have at least one letter
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        return True
    
    def _normalize_artist(self, name: str) -> str:
        """Normalize artist name to proper case"""
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Handle "X" separators (collaborations)
        if ' x ' in name.lower():
            parts = re.split(r'\s+x\s+', name, flags=re.IGNORECASE)
            return ' X '.join(' '.join(word.capitalize() for word in part.split()) for part in parts)
        
        # Capitalize each word
        return ' '.join(word.capitalize() for word in name.split())
    
    def search_youtube_with_api(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search YouTube using Data API v3
        """
        if not self.youtube_api_key:
            logger.warning("YouTube API key not found. Using yt-dlp fallback.")
            return []
        
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            
            youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
            
            search_response = youtube.search().list(
                q=query,
                part='id,snippet',
                type='video',
                maxResults=min(max_results, 50),  # API limit
                order='viewCount',  # Sort by views (most popular)
                videoCategoryId='10'  # Music category
            ).execute()
            
            videos = []
            for item in search_response.get('items', []):
                video_id = item['id']['videoId']
                snippet = item['snippet']
                
                # Get video statistics
                try:
                    stats_response = youtube.videos().list(
                        part='statistics',
                        id=video_id
                    ).execute()
                    
                    stats = stats_response['items'][0]['statistics'] if stats_response['items'] else {}
                    
                    videos.append({
                        'id': video_id,
                        'title': snippet['title'],
                        'channel': snippet['channelTitle'],
                        'published': snippet['publishedAt'],
                        'view_count': int(stats.get('viewCount', 0)),
                        'like_count': int(stats.get('likeCount', 0)),
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })
                except Exception as e:
                    logger.warning(f"Error getting stats for {video_id}: {e}")
                    videos.append({
                        'id': video_id,
                        'title': snippet['title'],
                        'channel': snippet['channelTitle'],
                        'published': snippet['publishedAt'],
                        'view_count': 0,
                        'like_count': 0,
                        'url': f"https://www.youtube.com/watch?v={video_id}"
                    })
            
            return videos
            
        except ImportError:
            logger.warning("google-api-python-client not installed. Using yt-dlp fallback.")
            return []
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return []
    
    def search_youtube_with_ytdlp(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search YouTube using yt-dlp (fallback if API not available)
        """
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': 'ytsearch',
            }
            
            search_query = f"ytsearch{max_results}:{query}"
            videos = []
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            videos.append({
                                'id': entry.get('id', ''),
                                'title': entry.get('title', ''),
                                'channel': entry.get('uploader', ''),
                                'published': entry.get('upload_date', ''),
                                'view_count': entry.get('view_count', 0),
                                'like_count': entry.get('like_count', 0),
                                'url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                            })
            
            return videos
            
        except ImportError:
            logger.error("yt-dlp not installed. Install with: pip install yt-dlp")
            return []
        except Exception as e:
            logger.error(f"Error searching with yt-dlp: {e}")
            return []
    
    def discover_trending_artists(self, max_artists: int = 100) -> List[Tuple[str, int, Dict]]:
        """
        Discover trending type beat artists by analyzing YouTube searches
        
        Args:
            max_artists: Maximum number of artists to return
            
        Returns:
            List of (artist_name, count, metadata) tuples sorted by popularity
        """
        logger.info("🔍 Discovering trending type beat artists...")
        
        # Search queries to find type beats
        search_queries = [
            "type beat",  # General search
            "type beat 2024",
            "type beat 2025",
            "free type beat",
            "type beat instrumental",
            "hard type beat",
            "trap type beat",
            "rap type beat",
            "hip hop type beat",
        ]
        
        all_videos = []
        
        # Search each query
        for query in search_queries:
            logger.info(f"📊 Searching: '{query}'...")
            
            # Try API first, fallback to yt-dlp
            videos = self.search_youtube_with_api(query, max_results=50)
            if not videos:
                videos = self.search_youtube_with_ytdlp(query, max_results=50)
            
            all_videos.extend(videos)
            time.sleep(1)  # Rate limiting
        
        logger.info(f"📹 Found {len(all_videos)} total videos")
        
        # Extract artists from titles
        artist_data = defaultdict(lambda: {'count': 0, 'total_views': 0, 'videos': []})
        
        for video in all_videos:
            title = video.get('title', '')
            artists = self.extract_artist_from_title(title)
            
            for artist in artists:
                artist_data[artist]['count'] += 1
                artist_data[artist]['total_views'] += video.get('view_count', 0)
                artist_data[artist]['videos'].append({
                    'title': title,
                    'views': video.get('view_count', 0),
                    'url': video.get('url', '')
                })
        
        # Sort by: count first, then total views
        sorted_artists = sorted(
            artist_data.items(),
            key=lambda x: (x[1]['count'], x[1]['total_views']),
            reverse=True
        )
        
        # Return top artists
        top_artists = []
        for artist, data in sorted_artists[:max_artists]:
            top_artists.append((
                artist,
                data['count'],
                {
                    'total_views': data['total_views'],
                    'avg_views': data['total_views'] // max(data['count'], 1),
                    'sample_videos': sorted(data['videos'], key=lambda v: v['views'], reverse=True)[:3]
                }
            ))
        
        logger.info(f"✅ Discovered {len(top_artists)} trending artists")
        return top_artists
    
    def save_results(self, artists: List[Tuple[str, int, Dict]], filename: str = "trending_artists.json"):
        """
        Save discovered artists to JSON file
        """
        output_dir = Path("data")
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / filename
        
        results = {
            'discovered_at': time.time(),
            'total_artists': len(artists),
            'artists': [
                {
                    'name': artist,
                    'type_beat_count': count,
                    'total_views': data['total_views'],
                    'avg_views': data['avg_views'],
                    'sample_videos': data['sample_videos']
                }
                for artist, count, data in artists
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"💾 Saved results to {output_path}")
        return output_path
    
    def print_results(self, artists: List[Tuple[str, int, Dict]], top_n: int = 50):
        """
        Print top artists in a readable format
        """
        print(f"\n🎵 Top {top_n} Trending Type Beat Artists:\n")
        print(f"{'Rank':<6} {'Artist':<30} {'Type Beats':<15} {'Total Views':<15} {'Avg Views':<15}")
        print("-" * 90)
        
        for i, (artist, count, data) in enumerate(artists[:top_n], 1):
            total_views = data['total_views']
            avg_views = data['avg_views']
            
            # Format large numbers
            total_str = f"{total_views:,}" if total_views < 1_000_000_000 else f"{total_views/1_000_000_000:.1f}B"
            avg_str = f"{avg_views:,}" if avg_views < 1_000_000 else f"{avg_views/1_000_000:.1f}M"
            
            print(f"{i:<6} {artist:<30} {count:<15} {total_str:<15} {avg_str:<15}")
        
        print(f"\n✅ Total artists discovered: {len(artists)}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover trending type beat artists")
    parser.add_argument("--max-artists", type=int, default=100,
                       help="Maximum number of artists to discover")
    parser.add_argument("--top-n", type=int, default=50,
                       help="Number of top artists to display")
    parser.add_argument("--save", action="store_true",
                       help="Save results to JSON file")
    
    args = parser.parse_args()
    
    discoverer = TrendingArtistDiscoverer()
    artists = discoverer.discover_trending_artists(max_artists=args.max_artists)
    
    discoverer.print_results(artists, top_n=args.top_n)
    
    if args.save:
        discoverer.save_results(artists)
    
    return artists


if __name__ == "__main__":
    main()
