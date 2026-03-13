"""
Shadow PC Webhook Server
Receives training requests from Cloud Run backend
Handles YouTube downloads and fingerprint training
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
import logging
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.hybrid_trainer import HybridTrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Shadow PC Training Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global trainer instance
trainer_instance = None

# Request models
class TrainingRequest(BaseModel):
    artists: List[str]
    max_per_artist: int = 5
    clear_existing: bool = False


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "message": "Shadow PC Training Server",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health():
    """Health check for Cloud Run backend"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/train/start")
async def start_training(request: TrainingRequest):
    """
    Start training on Shadow PC
    This endpoint is called by Cloud Run backend
    """
    global trainer_instance

    # Check if training is already running
    if trainer_instance is not None and trainer_instance.is_running:
        logger.warning("⚠️  Training already in progress")
        raise HTTPException(
            status_code=400,
            detail="Training is already running. Wait for completion."
        )

    try:
        logger.info("="*60)
        logger.info("🚀 STARTING TRAINING ON SHADOW PC")
        logger.info(f"📊 Artists: {', '.join(request.artists)}")
        logger.info(f"🎵 Max per artist: {request.max_per_artist}")
        logger.info(f"🗑️  Clear existing: {request.clear_existing}")
        logger.info("="*60)

        # Create trainer instance
        trainer_instance = HybridTrainer()

        # Start training in background
        asyncio.create_task(run_training(trainer_instance, request))

        return {
            "status": "started",
            "message": "Training started on Shadow PC",
            "artists": request.artists,
            "max_per_artist": request.max_per_artist,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error starting training: {e}", exc_info=True)
        trainer_instance = None
        raise HTTPException(
            status_code=500,
            detail=f"Error starting training: {str(e)}"
        )


async def run_training(trainer: HybridTrainer, request: TrainingRequest):
    """
    Run training in background task
    """
    try:
        logger.info("🔄 Starting background training task...")

        # Run the training
        results = await trainer.train_from_youtube(
            artists=request.artists,
            max_per_artist=request.max_per_artist,
            clear_existing=request.clear_existing
        )

        logger.info("="*60)
        logger.info("✅ TRAINING COMPLETED")
        logger.info(f"📊 Results: {results}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"❌ Training failed: {e}", exc_info=True)
    finally:
        # Clear trainer instance
        trainer_instance = None


@app.get("/train/status")
async def get_training_status():
    """Get current training status"""
    global trainer_instance

    if trainer_instance is None:
        return {
            "is_training": False,
            "status": "idle",
            "progress": 0,
            "message": "No training in progress",
            "timestamp": datetime.now().isoformat()
        }

    # Get status from trainer
    status = trainer_instance.get_status()

    # Add timestamp
    status["timestamp"] = datetime.now().isoformat()

    return status


@app.post("/train/stop")
async def stop_training():
    """Stop currently running training"""
    global trainer_instance

    if trainer_instance is None:
        raise HTTPException(
            status_code=400,
            detail="No training is currently running"
        )

    try:
        logger.info("🛑 Stopping training...")
        trainer_instance.stop_training()
        trainer_instance = None

        return {
            "success": True,
            "message": "Training stopped",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error stopping training: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping training: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))

    logger.info("="*60)
    logger.info("🖥️  SHADOW PC TRAINING SERVER")
    logger.info(f"🔗 Listening on http://0.0.0.0:{port}")
    logger.info("📡 Ready to receive training requests")
    logger.info("="*60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
