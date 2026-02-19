"""
Integrations with existing music fingerprint databases
No need to upload songs - query against existing databases
"""

import requests
import logging
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Try to auto-configure ACRCloud using Personal Access Token
try:
    from .acrcloud_console_api import ACRCloudConsoleAPI
    console_api = ACRCloudConsoleAPI()
    if console_api.auto_configure():
        logger.info("ACRCloud credentials auto-configured from Personal Access Token")
except Exception as e:
    logger.debug(f"Could not auto-configure ACRCloud: {e}")


class AcoustIDService:
    """
    AcoustID (MusicBrainz) - Free, open source music fingerprint database
    Has millions of songs already fingerprinted
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: AcoustID API key (get free key from https://acoustid.org/api-key)
        """
        self.api_key = api_key or os.getenv("ACOUSTID_API_KEY")
        self.base_url = "https://api.acoustid.org/v2"
        
        if not self.api_key:
            logger.warning("AcoustID API key not set. Get free key from https://acoustid.org/api-key")
    
    def identify_audio(self, audio_file_path: str) -> List[Dict]:
        """
        Identify audio file using AcoustID fingerprint
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            List of matches with artist, title, and MusicBrainz IDs
        """
        if not self.api_key:
            return []
        
        try:
            import chromaprint  # pip install pyacoustid (includes chromaprint)
            import acoustid
            
            # Generate fingerprint
            duration, fingerprint = acoustid.fingerprint_file(audio_file_path)
            
            # Query AcoustID
            response = requests.get(
                f"{self.base_url}/lookup",
                params={
                    "client": self.api_key,
                    "duration": int(duration),
                    "fingerprint": fingerprint,
                    "meta": "recordings",  # Get recording metadata
                }
            )
            
            if response.status_code != 200:
                logger.error(f"AcoustID API error: {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            for result in data.get("results", []):
                if result.get("score", 0) > 0.5:  # Confidence threshold
                    for recording in result.get("recordings", []):
                        artists = [a.get("name", "") for a in recording.get("artists", [])]
                        results.append({
                            "artist": ", ".join(artists) if artists else "Unknown",
                            "title": recording.get("title", "Unknown"),
                            "score": result.get("score", 0),
                            "mbid": recording.get("id"),  # MusicBrainz ID
                            "source": "acoustid"
                        })
            
            logger.info(f"AcoustID found {len(results)} matches")
            return results
            
        except ImportError:
            logger.error("pyacoustid not installed. Install with: pip install pyacoustid")
            return []
        except Exception as e:
            logger.error(f"Error querying AcoustID: {e}", exc_info=True)
            return []


class ACRCloudService:
    """
    ACRCloud - Commercial music recognition API
    Free tier: 1000 requests/month
    Has huge database of songs
    """
    
    def __init__(self, access_key: Optional[str] = None, 
                 access_secret: Optional[str] = None,
                 host: Optional[str] = None):
        """
        Args:
            access_key: ACRCloud access key
            access_secret: ACRCloud access secret
            host: ACRCloud host (region-specific, defaults to EU if not provided)
        """
        self.access_key = access_key or os.getenv("ACRCLOUD_ACCESS_KEY")
        self.access_secret = access_secret or os.getenv("ACRCLOUD_ACCESS_SECRET")
        self.host = host or os.getenv("ACRCLOUD_HOST", "identify-eu-west-1.acrcloud.com")
        
        # If credentials not set, try to get from Console API using Personal Access Token
        if not self.access_key or not self.access_secret:
            try:
                from .acrcloud_console_api import ACRCloudConsoleAPI
                console_api = ACRCloudConsoleAPI()
                credentials = console_api.get_project_credentials()
                if credentials:
                    self.access_key = credentials["access_key"]
                    self.access_secret = credentials["access_secret"]
                    self.host = credentials["host"]
                    logger.info("✅ ACRCloud credentials fetched using Personal Access Token")
            except Exception as e:
                logger.debug(f"Could not fetch credentials from Console API: {e}")
        
        if not self.access_key or not self.access_secret:
            logger.warning("ACRCloud credentials not set. Sign up at https://www.acrcloud.com")
    
    def identify_audio(self, audio_file_path: str) -> List[Dict]:
        """
        Identify audio using ACRCloud
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            List of matches with artist, title, and metadata
        """
        if not self.access_key or not self.access_secret:
            return []
        
        try:
            import hashlib
            import base64
            import hmac
            import time
            
            # Read audio file
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            # Generate signature
            timestamp = str(int(time.time()))
            string_to_sign = f"POST\n/v1/identify\n{self.access_key}\naudio\n1\n{timestamp}"
            signature = base64.b64encode(
                hmac.new(
                    self.access_secret.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    hashlib.sha1
                ).digest()
            ).decode('utf-8')
            
            # Prepare request according to ACRCloud docs
            # sample must be a file upload, other params go in data
            sample_bytes = len(audio_data)
            files = [
                ('sample', ('audio.mp3', audio_data, 'audio/mpeg'))
            ]
            data = {
                'access_key': self.access_key,
                'sample_bytes': str(sample_bytes),
                'timestamp': timestamp,
                'signature': signature,
                'data_type': 'audio',
                'signature_version': '1'
            }
            
            # Query ACRCloud
            response = requests.post(
                f"https://{self.host}/v1/identify",
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                logger.error(f"ACRCloud API error: {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            if data.get("status", {}).get("code") == 0:
                for track in data.get("metadata", {}).get("music", []):
                    results.append({
                        "artist": track.get("artists", [{}])[0].get("name", "Unknown"),
                        "title": track.get("title", "Unknown"),
                        "album": track.get("album", {}).get("name", ""),
                        "score": track.get("score", 0) / 100.0,  # Convert to 0-1
                        "source": "acrcloud"
                    })
            
            logger.info(f"ACRCloud found {len(results)} matches")
            return results
            
        except Exception as e:
            logger.error(f"Error querying ACRCloud: {e}", exc_info=True)
            return []


class AuddIOService:
    """
    Audd.io - Music recognition API
    Free tier: 100 requests/month
    """
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Args:
            api_token: Audd.io API token (get from https://audd.io/)
        """
        self.api_token = api_token or os.getenv("AUDDIO_API_TOKEN")
        self.base_url = "https://api.audd.io"
        
        if not self.api_token:
            logger.warning("Audd.io API token not set. Get from https://audd.io/")
    
    def identify_audio(self, audio_file_path: str) -> List[Dict]:
        """
        Identify audio using Audd.io
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            List of matches with artist, title, and metadata
        """
        if not self.api_token:
            return []
        
        try:
            with open(audio_file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'api_token': self.api_token,
                    'return': 'spotify,apple_music'  # Get streaming links too
                }
                
                response = requests.post(
                    f"{self.base_url}/",
                    files=files,
                    data=data
                )
            
            if response.status_code != 200:
                logger.error(f"Audd.io API error: {response.status_code}")
                return []
            
            data = response.json()
            results = []
            
            if data.get("status") == "success" and data.get("result"):
                result = data["result"]
                results.append({
                    "artist": result.get("artist", "Unknown"),
                    "title": result.get("title", "Unknown"),
                    "album": result.get("album", ""),
                    "score": result.get("score", 0) / 100.0,
                    "source": "auddio",
                    "spotify_id": result.get("spotify", {}).get("id") if result.get("spotify") else None
                })
            
            logger.info(f"Audd.io found {len(results)} matches")
            return results
            
        except Exception as e:
            logger.error(f"Error querying Audd.io: {e}", exc_info=True)
            return []


class MusicDatabaseAggregator:
    """
    Aggregates results from multiple music databases
    Queries all available services and returns best matches
    """
    
    def __init__(self):
        self.acoustid = AcoustIDService()
        self.acrcloud = ACRCloudService()
        self.auddio = AuddIOService()
    
    def identify_audio(self, audio_file_path: str, 
                      use_services: Optional[List[str]] = None) -> List[Dict]:
        """
        Query all available music databases
        
        Args:
            audio_file_path: Path to audio file
            use_services: List of services to use ['acoustid', 'acrcloud', 'auddio']
                         If None, uses all available
            
        Returns:
            Aggregated list of matches, sorted by confidence
        """
        use_services = use_services or ['acoustid', 'acrcloud', 'auddio']
        all_results = []
        
        if 'acoustid' in use_services:
            results = self.acoustid.identify_audio(audio_file_path)
            all_results.extend(results)
        
        if 'acrcloud' in use_services:
            results = self.acrcloud.identify_audio(audio_file_path)
            all_results.extend(results)
        
        if 'auddio' in use_services:
            results = self.auddio.identify_audio(audio_file_path)
            all_results.extend(results)
        
        # Sort by score and deduplicate
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Simple deduplication (same artist + title)
        seen = set()
        unique_results = []
        for result in all_results:
            key = (result.get('artist', '').lower(), result.get('title', '').lower())
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        logger.info(f"Found {len(unique_results)} unique matches from {len(use_services)} services")
        return unique_results
