"""
Model inference for type beat classification
Loads trained model and makes predictions
"""

import torch
import numpy as np
from typing import List, Tuple
import logging
import os

logger = logging.getLogger(__name__)


class ModelInference:
    """
    Handles model loading and inference
    For MVP: uses placeholder logic, will be replaced with actual trained model
    """
    
    def __init__(self, model_path: str = None):
        """
        Args:
            model_path: Path to trained model checkpoint
        """
        self.model_path = model_path or os.getenv("MODEL_PATH", "data/models/type_beat_classifier.pt")
        self.model = None
        self.artist_list = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # TODO: Load actual model when available
        # self._load_model()
    
    def _load_model(self):
        """Load trained PyTorch model"""
        if os.path.exists(self.model_path):
            try:
                checkpoint = torch.load(self.model_path, map_location=self.device)
                self.model = checkpoint['model']
                self.artist_list = checkpoint['artist_list']
                self.model.eval()
                logger.info(f"Loaded model from {self.model_path}")
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                raise
        else:
            logger.warning(f"Model not found at {self.model_path}, using placeholder")
    
    def predict(self, features: dict) -> List[Tuple[str, float]]:
        """
        Predict artist matches from audio features
        
        Args:
            features: Dictionary of audio features from AudioProcessor
        
        Returns:
            List of (artist_name, confidence_score) tuples, sorted by confidence
        """
        # Use trained model if available
        if self.model is not None:
            try:
                # Preprocess features for model
                from app.audio_processor import AudioProcessor
                processor = AudioProcessor()
                mel_spec = processor.preprocess_for_model(features)
                
                # Convert to tensor
                input_tensor = torch.from_numpy(mel_spec).float().to(self.device)
                
                # Run inference
                with torch.no_grad():
                    outputs = self.model(input_tensor)
                    probabilities = torch.softmax(outputs, dim=1)
                    probs = probabilities[0].cpu().numpy()
                
                # Get top predictions
                top_indices = np.argsort(probs)[::-1][:5]  # Top 5
                predictions = [
                    (self.artist_list[idx], float(probs[idx]))
                    for idx in top_indices
                    if probs[idx] > 0.1  # Filter low confidence
                ]
                
                return predictions
            except Exception as e:
                logger.error(f"Error during model inference: {str(e)}")
                # Fall through to feature-based classifier
        
        # NO FALLBACKS - If no trained model, return empty
        # Fingerprint matching should be used instead via /api/analyze
        logger.warning("No trained model available. Use fingerprint matching instead.")
        return []
    
    # REMOVED: _placeholder_predictions() - No fallbacks, only real analysis
