"""
FastAPI Backend for Type Beat Analyzer
Main API endpoints for audio upload, analysis, and trending data
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.trending_service import TrendingService
from app.database import get_db
from app.schemas import AnalysisResult, TrendingArtist, FingerprintMatch, FingerprintUpload, FingerprintStats
from app.processing_monitor import ProcessingMonitor
from app.fingerprint_service import FingerprintService
from app.music_database_apis import MusicDatabaseAggregator

load_dotenv()

app = FastAPI(
    title="Type Beat Analyzer API",
    description="Shazam for type beats - analyze your beat and see trending artists",
    version="0.1.0"
)

# CORS middleware - allow local + remote access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for remote demo (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (with optional audio processing)
try:
    from app.audio_processor import AudioProcessor
    from app.model_inference import ModelInference
    audio_processor = AudioProcessor()
    model_inference = ModelInference()
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Audio processing not available: {e}")
    print("   Trending features will still work!")
    audio_processor = None
    model_inference = None
    AUDIO_PROCESSING_AVAILABLE = False

trending_service = TrendingService()
processing_monitor = ProcessingMonitor()
fingerprint_service = FingerprintService()
music_db = MusicDatabaseAggregator()  # Query existing music databases


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Type Beat Analyzer API",
        "version": "0.1.0"
    }


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze_beat(
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    """
    Analyze uploaded beat using fingerprint matching
    Returns similar beats from database with similarity scores
    """
    if not AUDIO_PROCESSING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Audio processing not available. Please install librosa: conda install -c conda-forge librosa"
        )
    
    import time
    import uuid
    
    temp_path = None
    start_time = time.time()
    job_id = None
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an audio file"
            )
        
        # Create processing job
        job_id = processing_monitor.create_job(file.filename or "unknown")
        processing_monitor.update_job(job_id, status="processing", stage="Uploading file", progress=10)
        
        # Generate unique temp file name to avoid conflicts
        file_ext = os.path.splitext(file.filename or "audio")[1] or ".wav"
        temp_path = f"/tmp/typebeat_{uuid.uuid4().hex}{file_ext}"
        
        # Save uploaded file temporarily
        processing_monitor.update_job(job_id, stage="Saving file", progress=20)
        with open(temp_path, "wb") as f:
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is empty"
                )
            f.write(content)
        
        # Try music database APIs first (existing databases)
        processing_monitor.update_job(job_id, stage="Querying music databases", progress=40)
        logger.info(f"[Job {job_id}] Querying existing music databases for {file.filename}")
        
        db_matches = music_db.identify_audio(temp_path)
        
        # Also search local fingerprint database
        processing_monitor.update_job(job_id, stage="Searching local database", progress=60)
        local_matches = fingerprint_service.search_similar(temp_path, top_k=5, threshold=0.5)
        
        # Combine results (prefer database matches, then local)
        all_matches = []
        seen_artists = set()
        
        # Add database matches first (higher confidence)
        for match in db_matches[:3]:  # Top 3 from databases
            artist = match.get('artist', 'Unknown')
            if artist not in seen_artists:
                seen_artists.add(artist)
                all_matches.append({
                    'artist': artist,
                    'title': match.get('title', ''),
                    'similarity': match.get('score', 0.8),
                    'source': match.get('source', 'database')
                })
        
        # Add local matches
        for match in local_matches:
            artist = match.get('artist', 'Unknown')
            if artist not in seen_artists:
                seen_artists.add(artist)
                all_matches.append({
                    'artist': artist,
                    'title': match.get('title', ''),
                    'similarity': match.get('similarity', 0.5),
                    'source': 'local'
                })
        
        logger.info(f"[Job {job_id}] Found {len(all_matches)} total matches ({len(db_matches)} from databases, {len(local_matches)} local)")
        
        if not all_matches:
            # No matches found - return empty result (NO FAKE PREDICTIONS)
            processing_monitor.update_job(
                job_id,
                status="completed",
                stage="No matches found",
                progress=100,
                completed_at=datetime.now().isoformat(),
                results=[]
            )
            return AnalysisResult(
                matches=[],
                processing_time_ms=round((time.time() - start_time) * 1000, 2)
            )
        
        # Get trending data for matched artists
        processing_monitor.update_job(job_id, stage="Fetching trending data", progress=80)
        results = []
        
        for match in all_matches:
            artist = match['artist']
            trending = await trending_service.get_trending_data(artist)
            results.append({
                "artist": artist,
                "confidence": match['similarity'],
                "trending": trending
            })
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        processing_monitor.update_job(
            job_id,
            status="completed",
            stage="Complete",
            progress=100,
            completed_at=datetime.now().isoformat(),
            results=results
        )
        
        logger.info(f"[Job {job_id}] Analysis complete in {processing_time:.2f}ms - {len(results)} matches")
        
        return AnalysisResult(
            matches=results,
            processing_time_ms=round(processing_time, 2)
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        if job_id:
            processing_monitor.update_job(job_id, status="failed", progress=0)
        raise
    except Exception as e:
        logger.error(f"[Job {job_id}] Error processing audio: {str(e)}", exc_info=True)
        if job_id:
            processing_monitor.update_job(
                job_id,
                status="failed",
                error=str(e),
                progress=0
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )
    finally:
        # Always clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_path}: {str(e)}")


@app.get("/api/trending", response_model=List[TrendingArtist])
async def get_trending_artists(
    limit: int = 20,
    db=Depends(get_db)
):
    """
    Get list of currently trending artists for type beats
    """
    try:
        trending = await trending_service.get_top_trending(limit=limit)
        return trending
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching trending data: {str(e)}"
        )


@app.get("/api/artists/{artist_name}/trending")
async def get_artist_trending(artist_name: str):
    """
    Get detailed trending data for a specific artist
    """
    try:
        trending = await trending_service.get_trending_data(artist_name)
        return trending
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching artist data: {str(e)}"
        )


@app.get("/api/processing")
async def get_recent_jobs(limit: int = 10):
    """
    Get recent processing jobs
    """
    jobs = processing_monitor.get_all_jobs(limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


@app.get("/api/processing/{job_id}")
async def get_processing_status(job_id: str):
    """
    Get processing status for a job
    """
    job = processing_monitor.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/api/fingerprint/upload")
async def upload_fingerprint(
    file: UploadFile = File(...),
    artist: str = Form(...),
    title: str = Form(None),
    uploader_id: str = Form(None)
):
    """
    Upload a beat to fingerprint database (admin/curator endpoint)
    Requires artist name to tag the beat
    """
    if not artist:
        raise HTTPException(
            status_code=400,
            detail="Artist name is required"
        )
    
    if not AUDIO_PROCESSING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Audio processing not available"
        )
    
    import uuid
    
    temp_path = None
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an audio file"
            )
        
        # Save uploaded file temporarily
        file_ext = os.path.splitext(file.filename or "audio")[1] or ".wav"
        temp_path = f"/tmp/typebeat_upload_{uuid.uuid4().hex}{file_ext}"
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is empty"
                )
            f.write(content)
        
        # Add to fingerprint database
        fingerprint_id = fingerprint_service.add_fingerprint(
            audio_path=temp_path,
            artist=artist,
            title=title,
            uploader_id=uploader_id
        )
        
        logger.info(f"Uploaded fingerprint {fingerprint_id} for {artist}")
        
        return {
            "success": True,
            "fingerprint_id": fingerprint_id,
            "artist": artist,
            "title": title or file.filename
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading fingerprint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading fingerprint: {str(e)}"
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_path}: {str(e)}")


@app.post("/api/fingerprint/match", response_model=List[FingerprintMatch])
async def match_fingerprint(file: UploadFile = File(...)):
    """
    Match uploaded beat against fingerprint database
    Returns list of similar beats with similarity scores
    """
    if not AUDIO_PROCESSING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Audio processing not available"
        )
    
    import uuid
    
    temp_path = None
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an audio file"
            )
        
        # Save uploaded file temporarily
        file_ext = os.path.splitext(file.filename or "audio")[1] or ".wav"
        temp_path = f"/tmp/typebeat_match_{uuid.uuid4().hex}{file_ext}"
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is empty"
                )
            f.write(content)
        
        # Search for matches
        matches = fingerprint_service.search_similar(temp_path, top_k=10, threshold=0.5)
        
        return [FingerprintMatch(**match) for match in matches]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching fingerprint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error matching fingerprint: {str(e)}"
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to remove temp file {temp_path}: {str(e)}")


@app.get("/api/fingerprint/stats", response_model=FingerprintStats)
async def get_fingerprint_stats():
    """
    Get fingerprint database statistics
    """
    stats = fingerprint_service.get_stats()
    return FingerprintStats(**stats)


@app.post("/api/train/streaming")
async def train_from_streaming(artists: List[str] = Form(...), max_tracks: int = Form(50)):
    """
    Automated training endpoint - streams from Spotify, generates fingerprints
    Legal: Only stores fingerprints (not audio), deletes audio immediately
    """
    try:
        # Import here to avoid circular dependencies
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml'))
        from streaming_trainer import StreamingTrainer
        
        spotify_id = os.getenv("SPOTIFY_CLIENT_ID")
        spotify_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        
        if not spotify_id or not spotify_secret:
            raise HTTPException(
                status_code=400,
                detail="Spotify credentials not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env"
            )
        
        trainer = StreamingTrainer(spotify_id, spotify_secret)
        count = trainer.train_multiple_artists(artists, max_tracks)
        trainer.save_training_data("final_training_data.json")
        
        return {
            "success": True,
            "fingerprints_generated": count,
            "artists_trained": artists,
            "message": f"Generated {count} fingerprints from {len(artists)} artists"
        }
        
    except Exception as e:
        logger.error(f"Error in streaming training: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error training from streaming: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
