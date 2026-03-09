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

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ml.hybrid_trainer import HybridTrainer
from app.fingerprint_service_cloud_storage import CloudStorageUploader

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
    "total_fingerprints": 0
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
    message: str


def run_training_task(artists: List[str], max_per_artist: int):
    """Background task to run training"""
    global training_status

    try:
        training_status["is_training"] = True
        training_status["started_at"] = datetime.now().isoformat()

        logger.info(f"🚀 Starting training on Shadow PC for {len(artists)} artists")

        # Initialize trainer with API keys from environment
        trainer = HybridTrainer(
            youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
        )

        # Initialize Cloud Storage uploader
        uploader = CloudStorageUploader()

        total_fingerprints = 0

        # Process each artist
        for i, artist in enumerate(artists):
            if not training_status["is_training"]:
                logger.info("Training stopped")
                break

            training_status["current_artist"] = artist
            logger.info(f"[{i+1}/{len(artists)}] Training on: {artist}")

            try:
                # Train on this artist
                count = trainer.train_artist_hybrid(artist, max_items=max_per_artist)

                if count > 0:
                    logger.info(f"✅ Generated {count} fingerprints for {artist}")

                    # Convert to Cloud Storage format
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

                    # Upload to Cloud Storage
                    logger.info(f"📤 Uploading {len(artist_fingerprints)} fingerprints...")
                    uploader.upload_training_results(artist_fingerprints)
                    total_fingerprints += count

            except Exception as e:
                logger.error(f"❌ Error training on {artist}: {e}")
                continue

        # Update status
        training_status["is_training"] = False
        training_status["current_artist"] = None
        training_status["last_completed"] = datetime.now().isoformat()
        training_status["total_fingerprints"] = total_fingerprints

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
