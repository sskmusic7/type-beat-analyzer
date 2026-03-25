#!/usr/bin/env python3
"""
Shadow PC Webhook Server
Receives training requests from Cloud Run admin panel
Runs training on Shadow PC (YouTube works here!)
Uploads fingerprints to Cloud Storage
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

from dotenv import load_dotenv
# Load .env from the same directory as this script
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from ml.hybrid_trainer import HybridTrainer
from app.fingerprint_service_cloud_storage import CloudStorageUploader
from audio_dna import AudioDNA, ArtistDNA, BlendEngine
from audio_dna.gcs_storage import DNAStorage
from app.fingerprint_service import FingerprintService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shadow_pc_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Shadow PC Training Server",
    description="Receives training requests from Type Beat admin panel"
)

# Global state
training_status = {
    "is_training": False,
    "current_artist": None,
    "started_at": None,
    "last_completed": None,
    "total_fingerprints": 0,
    "completed_artists": 0,
    "total_artists": 0,
    "progress": 0,
    "logs": []
}

# Request models
class TrainingRequest(BaseModel):
    artists: List[str]
    max_per_artist: int = 5
    clear_existing: bool = False


class HealthResponse(BaseModel):
    status: str
    message: str
    is_training: bool
    shadow_pc_ip: str


class TrainingStatusResponse(BaseModel):
    is_training: bool
    current_artist: Optional[str]
    started_at: Optional[str]
    last_completed: Optional[str]
    total_fingerprints: int
    completed_artists: int = 0
    total_artists: int = 0
    progress: float = 0
    logs: List[str] = []
    message: str


def _download_faiss_from_gcs():
    """Download current FAISS index + metadata from GCS to local data/models/"""
    from google.cloud import storage

    bucket_name = os.getenv("FINGERPRINT_BUCKET_NAME", "type-beat-fingerprints")
    local_dir = Path("data/models")
    local_dir.mkdir(parents=True, exist_ok=True)

    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        index_blob = bucket.blob("models/fingerprint_index.faiss")
        if index_blob.exists():
            index_blob.download_to_filename(str(local_dir / "fingerprint_index.faiss"))
            logger.info("📥 Downloaded FAISS index from GCS")

        metadata_blob = bucket.blob("models/fingerprint_metadata.json")
        if metadata_blob.exists():
            metadata_blob.download_to_filename(str(local_dir / "fingerprint_metadata.json"))
            logger.info("📥 Downloaded metadata from GCS")
    except Exception as e:
        logger.warning(f"⚠️  Could not download from GCS: {e}")


def _sync_faiss_to_gcs(uploader: CloudStorageUploader):
    """
    Download current FAISS index + metadata from GCS,
    rebuild with any new local fingerprints, and re-upload.
    This ensures GCS always has the complete, up-to-date index.
    """
    import tempfile
    from google.cloud import storage

    bucket_name = os.getenv("FINGERPRINT_BUCKET_NAME", "type-beat-fingerprints")
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Use the local FingerprintService data dir (where training saved results)
    local_index = Path("data/models/fingerprint_index.faiss")
    local_metadata = Path("data/models/fingerprint_metadata.json")

    if local_index.exists() and local_metadata.exists():
        # Upload the local FAISS index (which now includes new fingerprints)
        bucket.blob("models/fingerprint_index.faiss").upload_from_filename(str(local_index))
        bucket.blob("models/fingerprint_metadata.json").upload_from_filename(str(local_metadata))
        logger.info(f"✅ Uploaded FAISS index + metadata to GCS")
    else:
        logger.warning("⚠️  Local FAISS index not found, skipping GCS sync")


def _trigger_cloud_run_refresh():
    """Tell Cloud Run to reload fingerprints from GCS"""
    import requests as req
    cloud_run_url = os.getenv("CLOUD_RUN_URL", "https://type-beat-backend-287783957820.us-central1.run.app")
    try:
        resp = req.post(
            f"{cloud_run_url}/api/fingerprint/refresh",
            timeout=30
        )
        if resp.status_code == 200:
            logger.info(f"✅ Cloud Run refresh triggered: {resp.json()}")
        else:
            logger.warning(f"⚠️  Cloud Run refresh returned {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"⚠️  Could not trigger Cloud Run refresh (will sync on next restart): {e}")


def run_training_task(artists: List[str], max_per_artist: int):
    """Background task to run training"""
    global training_status

    try:
        training_status["is_training"] = True
        training_status["started_at"] = datetime.now().isoformat()
        training_status["completed_artists"] = 0
        training_status["total_artists"] = len(artists)
        training_status["progress"] = 0
        training_status["logs"] = [f"Starting training for {len(artists)} artists..."]

        logger.info(f"🚀 Starting training on Shadow PC for {len(artists)} artists")

        # Initialize trainer with API keys from environment
        trainer = HybridTrainer(
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
        )

        # Initialize Cloud Storage uploader
        uploader = CloudStorageUploader()

        # Download current FAISS index from GCS so we can add to it
        _download_faiss_from_gcs()
        fp_service = FingerprintService()
        logger.info(f"📥 Loaded existing FAISS index with {fp_service.index.ntotal} fingerprints")

        total_fingerprints = 0

        # Process each artist
        for i, artist in enumerate(artists):
            if not training_status["is_training"]:
                logger.info("Training stopped")
                break

            training_status["current_artist"] = artist
            training_status["progress"] = round((i / len(artists)) * 100, 1)
            training_status["logs"].append(f"[{i+1}/{len(artists)}] Training: {artist}")
            logger.info(f"[{i+1}/{len(artists)}] Training on: {artist}")

            try:
                # Train on this artist
                count = trainer.train_artist_hybrid(artist, max_items=max_per_artist)

                if count > 0:
                    logger.info(f"✅ Generated {count} fingerprints for {artist}")

                    # Add to local FAISS index
                    for item in trainer.training_data:
                        if item.get('artist') == artist and item.get('fingerprint'):
                            embedding = np.array(item['fingerprint'], dtype=np.float32).reshape(1, -1)
                            fp_service.index.add(embedding)
                            fp_service.metadata.append({
                                'id': fp_service.id_counter,
                                'artist': item.get('artist', artist),
                                'title': item.get('track_name', 'Unknown'),
                                'audio_hash': f"shadow_pc_{artist}_{fp_service.id_counter}",
                                'upload_date': datetime.now().isoformat(),
                                'uploader_id': 'shadow_pc_training'
                            })
                            fp_service.id_counter += 1

                    # Save updated FAISS index locally
                    fp_service._save_index()
                    logger.info(f"📊 FAISS index now has {fp_service.index.ntotal} fingerprints")

                    # Also upload individual .npz files to GCS
                    artist_fingerprints = [
                        {
                            'id': f"{artist}_{j}_{hash(os.urandom(8))}",
                            'artist': item.get('artist', artist),
                            'title': item.get('track_name', 'Unknown'),
                            'embedding': item.get('fingerprint'),
                            'source': 'youtube_download',
                            'upload_date': datetime.now().isoformat()
                        }
                        for j, item in enumerate(trainer.training_data)
                        if item.get('artist') == artist
                    ]
                    uploader.upload_training_results(artist_fingerprints)
                    total_fingerprints += count
                    training_status["logs"].append(f"✅ {artist}: {count} fingerprints")
                else:
                    training_status["logs"].append(f"⚠️ {artist}: 0 fingerprints (no results)")

                training_status["completed_artists"] = i + 1
                training_status["total_fingerprints"] = total_fingerprints
                training_status["progress"] = round(((i + 1) / len(artists)) * 100, 1)

            except Exception as e:
                logger.error(f"❌ Error training on {artist}: {e}")
                training_status["logs"].append(f"❌ {artist}: error - {str(e)[:80]}")
                training_status["completed_artists"] = i + 1
                training_status["progress"] = round(((i + 1) / len(artists)) * 100, 1)
                continue

        # Sync updated FAISS index + metadata back to GCS
        if total_fingerprints > 0:
            try:
                logger.info("📤 Syncing FAISS index + metadata to GCS...")
                _sync_faiss_to_gcs(uploader)
                logger.info("✅ FAISS index synced to GCS")

                # Trigger Cloud Run refresh
                _trigger_cloud_run_refresh()
            except Exception as e:
                logger.error(f"❌ Error syncing to GCS: {e}")

        # Update status
        training_status["is_training"] = False
        training_status["current_artist"] = None
        training_status["last_completed"] = datetime.now().isoformat()
        training_status["total_fingerprints"] = total_fingerprints
        training_status["progress"] = 100
        training_status["logs"].append(f"🏁 Training complete! {total_fingerprints} fingerprints from {len(artists)} artists")

        logger.info(f"✅ Training complete! Generated {total_fingerprints} fingerprints")

    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        training_status["is_training"] = False
        training_status["current_artist"] = None


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        message="Shadow PC Training Server is running",
        is_training=training_status["is_training"],
        shadow_pc_ip=os.getenv("SHADOW_PC_IP", "unknown")
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check for Cloud Run to monitor Shadow PC"""
    return HealthResponse(
        status="ok",
        message="Shadow PC Training Server is running",
        is_training=training_status["is_training"],
        shadow_pc_ip=os.getenv("SHADOW_PC_IP", "unknown")
    )


@app.post("/train/start")
async def start_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Start training in background - called from Cloud Run admin panel"""

    if training_status["is_training"]:
        raise HTTPException(
            status_code=400,
            detail="Training is already in progress"
        )

    logger.info(f"📥 Received training request from admin panel")
    logger.info(f"   Artists: {', '.join(request.artists)}")
    logger.info(f"   Max per artist: {request.max_per_artist}")

    # Start training in background
    background_tasks.add_task(
        run_training_task,
        request.artists,
        request.max_per_artist
    )

    return {
        "success": True,
        "message": "Training started on Shadow PC",
        "artists": request.artists,
        "max_per_artist": request.max_per_artist
    }


@app.get("/train/status", response_model=TrainingStatusResponse)
async def get_training_status():
    """Get current training status"""
    return TrainingStatusResponse(
        is_training=training_status["is_training"],
        current_artist=training_status["current_artist"],
        started_at=training_status["started_at"],
        last_completed=training_status["last_completed"],
        total_fingerprints=training_status["total_fingerprints"],
        completed_artists=training_status["completed_artists"],
        total_artists=training_status["total_artists"],
        progress=training_status["progress"],
        logs=training_status["logs"][-20:],
        message="Training in progress" if training_status["is_training"] else "Idle"
    )


@app.post("/train/stop")
async def stop_training():
    """Stop current training"""
    if not training_status["is_training"]:
        raise HTTPException(
            status_code=400,
            detail="No training in progress"
        )

    training_status["is_training"] = False
    logger.info("🛑 Training stopped by admin panel")

    return {
        "success": True,
        "message": "Training stopped"
    }


# ── Audio DNA Endpoints ──────────────────────────────────────

class DNAAnalyzeRequest(BaseModel):
    audio_path: str
    artist: Optional[str] = None
    enable_stems: bool = False

class DNABuildArtistRequest(BaseModel):
    artist: str
    audio_paths: List[str]
    enable_stems: bool = False
    upload_gcs: bool = True

class DNABlendRequest(BaseModel):
    audio_path: str
    top_k: int = 5


@app.post("/dna/analyze")
async def dna_analyze(request: DNAAnalyzeRequest):
    """Generate AudioDNA profile for a single track."""
    try:
        dna = AudioDNA(enable_stems=request.enable_stems)
        if request.enable_stems:
            profile = dna.profile(request.audio_path)
        else:
            profile = dna.profile_fast(request.audio_path)
        vector = dna.to_vector(profile)
        profile["vector"] = vector
        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dna/build-artist")
async def dna_build_artist(request: DNABuildArtistRequest, background_tasks: BackgroundTasks):
    """Build artist DNA profile from multiple tracks (background task)."""
    def _build():
        try:
            builder = ArtistDNA(enable_stems=request.enable_stems)
            profile = builder.build_artist_profile(request.audio_paths, request.artist)
            if request.upload_gcs:
                storage = DNAStorage()
                storage.upload_artist_profile(profile)
            logger.info(f"Artist DNA built for {request.artist}")
        except Exception as e:
            logger.error(f"Artist DNA build failed: {e}")

    background_tasks.add_task(_build)
    return {"success": True, "message": f"Building artist DNA for {request.artist} in background"}


@app.post("/dna/blend")
async def dna_blend(request: DNABlendRequest):
    """Analyze a beat and return artist blend breakdown."""
    try:
        # Load blend engine from local profiles
        engine = BlendEngine()
        dna_dir = Path("data/artist_dna")
        if dna_dir.exists():
            engine.add_artists_from_dir(str(dna_dir))

        if engine.index.ntotal == 0:
            raise HTTPException(status_code=400, detail="No artist profiles loaded. Train artists first.")

        dna = AudioDNA(enable_stems=False)
        profile = dna.profile_fast(request.audio_path)
        vector = dna.to_vector(profile)
        result = engine.blend(vector, top_k=request.top_k)
        result["beat_profile"] = {
            "bpm": profile.get("features", {}).get("tempo", {}).get("bpm"),
            "key": profile.get("features", {}).get("key", {}).get("key_label"),
            "top_tags": [t["tag"] for t in profile.get("clap_tags", [])[:5]],
        }
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dna/artists")
async def dna_list_artists():
    """List all artist DNA profiles available locally."""
    dna_dir = Path("data/artist_dna")
    if not dna_dir.exists():
        return {"artists": []}
    profiles = []
    for p in sorted(dna_dir.glob("*.json")):
        try:
            import json as _json
            with open(p) as f:
                data = _json.load(f)
            profiles.append({
                "artist": data.get("artist", p.stem),
                "track_count": data.get("track_count", 0),
                "bpm_mean": data.get("tempo", {}).get("bpm_mean"),
                "top_key": data.get("key", {}).get("top_key"),
            })
        except Exception:
            continue
    return {"artists": profiles}


def main():
    """Start the webhook server"""
    import argparse

    parser = argparse.ArgumentParser(description="Shadow PC Training Webhook Server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )

    args = parser.parse_args()

    # Set Shadow PC IP
    os.environ["SHADOW_PC_IP"] = os.getenv("SHADOW_PC_IP", "46.247.137.210")

    logger.info("🚀 Starting Shadow PC Training Webhook Server")
    logger.info(f"   Listening on: http://{args.host}:{args.port}")
    logger.info(f"   Shadow PC IP: {os.environ['SHADOW_PC_IP']}")
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  GET  /              - Health check")
    logger.info("  GET  /health        - Health check")
    logger.info("  POST /train/start   - Start training")
    logger.info("  GET  /train/status  - Get training status")
    logger.info("  POST /train/stop    - Stop training")
    logger.info("  POST /dna/analyze   - AudioDNA profile for a track")
    logger.info("  POST /dna/build-artist - Build artist DNA (background)")
    logger.info("  POST /dna/blend     - Blend analysis (artist matching)")
    logger.info("  GET  /dna/artists   - List artist profiles")
    logger.info("")

    # Run server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
