"""
FastAPI Backend for Type Beat Analyzer
Main API endpoints for audio upload, analysis, and trending data
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from dotenv import load_dotenv

from app.audio_processor import AudioProcessor
from app.model_inference import ModelInference
from app.trending_service import TrendingService
from app.database import get_db
from app.schemas import AnalysisResult, TrendingArtist

load_dotenv()

app = FastAPI(
    title="Type Beat Analyzer API",
    description="Shazam for type beats - analyze your beat and see trending artists",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
audio_processor = AudioProcessor()
model_inference = ModelInference()
trending_service = TrendingService()


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
    Analyze uploaded beat and return artist matches with confidence scores
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an audio file"
            )
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        try:
            # Extract audio features
            features = audio_processor.extract_features(temp_path)
            
            # Run model inference
            predictions = model_inference.predict(features)
            
            # Get trending data for matched artists
            results = []
            for artist, confidence in predictions:
                trending = await trending_service.get_trending_data(artist)
                results.append({
                    "artist": artist,
                    "confidence": confidence,
                    "trending": trending
                })
            
            return AnalysisResult(
                matches=results,
                processing_time_ms=0  # TODO: track actual time
            )
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
