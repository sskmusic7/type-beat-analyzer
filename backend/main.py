"""
FastAPI Backend for Type Beat Analyzer
Main API endpoints for audio upload, analysis, and trending data
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.trending_service import TrendingService
from app.database import get_db
from app.schemas import AnalysisResult, TrendingArtist, FingerprintMatch, FingerprintUpload, FingerprintStats
from app.processing_monitor import ProcessingMonitor
from app.fingerprint_service import FingerprintService
from app.music_database_apis import MusicDatabaseAggregator
from app.training_service import TrainingService
from app.training_service_shadow_pc import ShadowPCTrainingService

load_dotenv()


def sync_fingerprints_from_gcs():
    """Download latest FAISS index + metadata from GCS before loading FingerprintService"""
    bucket_name = os.getenv("FINGERPRINT_BUCKET_NAME", "type-beat-fingerprints")
    local_dir = Path("data/models")
    local_dir.mkdir(parents=True, exist_ok=True)

    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # Download FAISS index
        index_blob = bucket.blob("models/fingerprint_index.faiss")
        if index_blob.exists():
            index_blob.download_to_filename(str(local_dir / "fingerprint_index.faiss"))
            logger.info(f"Downloaded FAISS index from gs://{bucket_name}/models/fingerprint_index.faiss")

        # Download metadata
        metadata_blob = bucket.blob("models/fingerprint_metadata.json")
        if metadata_blob.exists():
            metadata_blob.download_to_filename(str(local_dir / "fingerprint_metadata.json"))
            logger.info(f"Downloaded metadata from gs://{bucket_name}/models/fingerprint_metadata.json")

        logger.info("GCS fingerprint sync complete")
    except Exception as e:
        logger.warning(f"Could not sync from GCS (will use local files): {e}")

# Use Shadow PC for training when configured
SHADOW_PC_WEBHOOK_URL = os.getenv("SHADOW_PC_WEBHOOK_URL")
USE_SHADOW_PC = bool(SHADOW_PC_WEBHOOK_URL)
if USE_SHADOW_PC:
    logger.info(f"🖥️  Shadow PC training enabled: {SHADOW_PC_WEBHOOK_URL}")
    shadow_pc_service = ShadowPCTrainingService()
else:
    logger.info("ℹ️  Shadow PC not configured, using local training")
    shadow_pc_service = None

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

# Sync fingerprints from GCS before loading local service
sync_fingerprints_from_gcs()
fingerprint_service = FingerprintService()
music_db = MusicDatabaseAggregator()  # Query existing music databases
training_service = TrainingService()  # Background fingerprint training


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
        
        # Also search local fingerprint database for closest matches
        # Use threshold 0.3 (30% similarity) to get top 5 closest matches
        processing_monitor.update_job(job_id, stage="Searching local database", progress=60)
        local_matches = fingerprint_service.search_similar(temp_path, top_k=5, threshold=0.3)
        
        # Sort local matches by similarity (highest first) - these are the 5 closest
        local_matches.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        # Also save fingerprint of uploaded beat for future matching
        processing_monitor.update_job(job_id, stage="Saving uploaded beat fingerprint", progress=70)
        try:
            # Extract artist from filename if possible, otherwise use "Unknown"
            filename = file.filename or "unknown"
            # Try to extract artist from filename (e.g., "Artist - Title.mp3")
            artist_from_filename = "Unknown"
            if " - " in filename:
                artist_from_filename = filename.split(" - ")[0].strip()
            elif "Prod" in filename or "prod" in filename:
                # Try to extract producer name
                parts = filename.replace(".mp3", "").split()
                if "Prod" in parts or "prod" in parts:
                    idx = parts.index("Prod") if "Prod" in parts else parts.index("prod")
                    if idx > 0:
                        artist_from_filename = " ".join(parts[:idx])
            
            fingerprint_service.add_fingerprint(
                audio_path=temp_path,
                artist=artist_from_filename,
                title=filename,
                uploader_id="user_upload"
            )
            logger.info(f"[Job {job_id}] Saved fingerprint for uploaded beat: {filename}")
        except Exception as e:
            logger.warning(f"[Job {job_id}] Could not save fingerprint for uploaded beat: {e}")
        
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
        
        # Add local matches (top 5 closest, sorted by similarity descending)
        for match in local_matches:
            artist = match.get('artist', 'Unknown')
            if artist not in seen_artists:
                seen_artists.add(artist)
                all_matches.append({
                    'artist': artist,
                    'title': match.get('title', ''),
                    'similarity': match.get('similarity', 0.0),
                    'source': 'local'
                })
        
        # Sort all matches by similarity (highest first) - ensures top 5 closest are first
        all_matches.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        # Take top 5 closest
        all_matches = all_matches[:5]
        
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


@app.post("/api/fingerprint/refresh")
async def refresh_fingerprints():
    """
    Re-sync fingerprints from GCS and reload the FAISS index.
    Call this after Shadow PC training completes to pick up new fingerprints.
    """
    global fingerprint_service
    try:
        sync_fingerprints_from_gcs()
        fingerprint_service = FingerprintService()
        stats = fingerprint_service.get_stats()
        return {
            "success": True,
            "message": f"Reloaded {stats['total_fingerprints']} fingerprints from {stats['artists']} artists",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error refreshing fingerprints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error refreshing: {str(e)}")


@app.get("/api/fingerprint/visualization")
async def get_fingerprint_visualization():
    """
    Get fingerprint data for 3D visualization
    Returns metadata with computed 3D coordinates based on artist clustering
    """
    try:
        import numpy as np
        from sklearn.manifold import TSNE
        from sklearn.preprocessing import LabelEncoder
        
        all_fingerprints = fingerprint_service.metadata
        
        if len(all_fingerprints) < 3:
            return {
                "points": [],
                "message": "Not enough fingerprints for visualization (need at least 3)"
            }
        
        # Create artist-based features for dimensionality reduction
        # Group by artist and create features
        artists = [fp['artist'] for fp in all_fingerprints]
        le = LabelEncoder()
        artist_encoded = le.fit_transform(artists)
        
        # Create feature matrix: artist encoding + some metadata-based features
        features = []
        for fp in all_fingerprints:
            artist_idx = artist_encoded[all_fingerprints.index(fp)]
            # Simple features: artist, title length, etc.
            title_len = len(fp.get('title', '')) / 100.0  # Normalize
            features.append([artist_idx, title_len, hash(fp.get('artist', '')) % 100 / 100.0])
        
        features = np.array(features)
        
        # Use t-SNE to reduce to 3D
        if len(features) > 50:
            perplexity = min(30, len(features) - 1)
        else:
            perplexity = max(5, len(features) // 3)
        
        tsne = TSNE(n_components=3, perplexity=perplexity, random_state=42, n_iter=1000)
        coords_3d = tsne.fit_transform(features)
        
        # Prepare response
        points = []
        for i, fp in enumerate(all_fingerprints):
            points.append({
                "id": fp['id'],
                "artist": fp['artist'],
                "title": fp.get('title', 'Unknown'),
                "x": float(coords_3d[i][0]),
                "y": float(coords_3d[i][1]),
                "z": float(coords_3d[i][2]),
            })
        
        return {
            "points": points,
            "total": len(points)
        }
        
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating visualization: {str(e)}"
        )


@app.get("/api/fingerprint/list")
async def list_all_fingerprints(limit: int = 1000, offset: int = 0):
    """
    Get list of all trained fingerprints
    Returns all fingerprints with metadata for the training dashboard
    """
    try:
        # Get all metadata (fingerprints)
        all_fingerprints = fingerprint_service.metadata
        
        # Apply pagination
        total = len(all_fingerprints)
        paginated = all_fingerprints[offset:offset + limit]
        
        return {
            "fingerprints": paginated,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error listing fingerprints: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching fingerprints: {str(e)}"
        )


@app.get("/api/tasks")
async def get_all_tasks(limit: int = 50):
    """
    Get all tasks/jobs for Mission Control dashboard
    Returns tasks organized by status
    """
    try:
        # Cleanup old jobs first
        processing_monitor.cleanup_old_jobs(max_age_hours=24)
        
        # Get all jobs
        all_jobs = processing_monitor.get_all_jobs(limit=limit)
        
        # Organize by status (Kanban columns)
        tasks_by_status = {
            "queued": [],
            "processing": [],
            "completed": [],
            "failed": []
        }
        
        for job in all_jobs:
            status = job.get("status", "queued")
            # Map statuses to Kanban columns
            if status == "queued":
                tasks_by_status["queued"].append(job)
            elif status == "processing":
                tasks_by_status["processing"].append(job)
            elif status == "completed":
                tasks_by_status["completed"].append(job)
            elif status == "failed":
                tasks_by_status["failed"].append(job)
            else:
                tasks_by_status["queued"].append(job)
        
        return {
            "tasks": all_jobs,
            "by_status": tasks_by_status,
            "total": len(all_jobs)
        }
    except Exception as e:
        logger.error(f"Error getting tasks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching tasks: {str(e)}"
        )


@app.get("/api/tasks/{job_id}")
async def get_task(job_id: str):
    """
    Get specific task by job ID
    """
    task = processing_monitor.get_job(job_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


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


@app.post("/api/fingerprint/train/start")
async def start_training(request: Request):
    """
    Start fingerprint training in background
    Downloads from YouTube, generates comprehensive fingerprints, deletes audio immediately

    Accepts JSON: {"artists": ["Artist1", "Artist2"], "clear_existing": false, "max_per_artist": 5}
    Or form data for backward compatibility
    """
    try:
        # Try JSON first
        try:
            body = await request.json()
            artist_list = body.get("artists", [])
            clear_existing = body.get("clear_existing", False)  # Default to additive
            max_per_artist = body.get("max_per_artist", 5)

            # Handle both list and string formats
            if isinstance(artist_list, str):
                raw_items = [part.strip() for part in artist_list.replace("\n", ",").split(",")]
                artist_list = sorted({item for item in raw_items if item})
            elif isinstance(artist_list, list):
                artist_list = sorted({str(a).strip() for a in artist_list if a and str(a).strip()})
            else:
                artist_list = []
        except:
            # Fallback to form data for backward compatibility
            form_data = await request.form()
            artists_str = form_data.get("artists", "")
            clear_existing = form_data.get("clear_existing", "false").lower() == "true"
            max_per_artist = int(form_data.get("max_per_artist", 5))

            artist_list = None
            if artists_str:
                raw_items = [part.strip() for part in str(artists_str).replace("\n", ",").split(",")]
                artist_list = sorted({item for item in raw_items if item})

        # Validate that artists are provided
        if not artist_list or len(artist_list) == 0:
            raise HTTPException(
                status_code=400,
                detail="No artists provided. Please provide at least one artist name."
            )

        # Route to Shadow PC if configured
        if USE_SHADOW_PC and shadow_pc_service:
            logger.info(f"🖥️  Forwarding training to Shadow PC: {artist_list}")
            result = await shadow_pc_service.start_training(
                artists=artist_list,
                max_per_artist=max_per_artist,
                clear_existing=clear_existing
            )
            if not result.get("success"):
                raise HTTPException(
                    status_code=502,
                    detail=result.get("message", "Shadow PC training failed")
                )
            return {
                "success": True,
                "message": "Training started on Shadow PC",
                "status": {
                    "status": "running",
                    "progress": 0,
                    "current_artist": artist_list[0] if artist_list else None,
                    "artists_processed": 0,
                    "total_artists": len(artist_list),
                    "fingerprints_generated": 0,
                    "started_at": datetime.now().isoformat(),
                    "completed_at": None,
                    "error": None,
                    "logs": [f"Training forwarded to Shadow PC for {len(artist_list)} artists"]
                }
            }

        # Local training fallback
        if training_service.is_running():
            raise HTTPException(
                status_code=400,
                detail="Training is already running. Stop it first or wait for completion."
            )

        success = training_service.start_training(
            clear_existing=clear_existing,
            max_per_artist=max_per_artist,
            artists=artist_list
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to start training"
            )

        return {
            "success": True,
            "message": "Training started",
            "status": training_service.get_status()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting training: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error starting training: {str(e)}"
        )


@app.post("/api/fingerprint/train/stop")
async def stop_training():
    """
    Stop currently running training
    """
    try:
        # Route to Shadow PC if configured
        if USE_SHADOW_PC and shadow_pc_service:
            result = await shadow_pc_service.stop_training()
            return {
                "success": result.get("success", True),
                "message": result.get("message", "Stop requested on Shadow PC"),
                "status": {"status": "stopping"}
            }

        if not training_service.is_running():
            raise HTTPException(
                status_code=400,
                detail="No training is currently running"
            )

        training_service.stop_training()

        return {
            "success": True,
            "message": "Training stop requested",
            "status": training_service.get_status()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping training: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping training: {str(e)}"
        )


@app.get("/api/fingerprint/train/status")
async def get_training_status():
    """
    Get current training status and progress
    """
    try:
        # Route to Shadow PC if configured
        if USE_SHADOW_PC and shadow_pc_service:
            status = await shadow_pc_service.get_training_status()
            # Map Shadow PC status fields to what the frontend expects
            is_training = status.get("is_training", False)
            return {
                "status": "running" if is_training else ("completed" if status.get("last_completed") else "idle"),
                "progress": status.get("progress", 0),
                "current_artist": status.get("current_artist"),
                "artists_processed": status.get("completed_artists", 0),
                "total_artists": status.get("total_artists", 0),
                "fingerprints_generated": status.get("total_fingerprints", 0),
                "started_at": status.get("started_at"),
                "completed_at": status.get("last_completed"),
                "error": None,
                "logs": status.get("logs", []),
                "source": "shadow_pc"
            }

        return training_service.get_status()
    except Exception as e:
        logger.error(f"Error getting training status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting training status: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
