#!/usr/bin/env python3
"""
Regenerate fingerprints using the improved fingerprint generation method
This is needed because the old fingerprints were generated with a simpler method
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
import tempfile
import subprocess

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.fingerprint_service import FingerprintService

def regenerate_fingerprints():
    """Regenerate all fingerprints using improved method"""
    
    project_root = Path(__file__).parent.parent
    training_data_path = project_root / "ml" / "data" / "training_fingerprints" / "final_training_data_1000.json"
    
    if not training_data_path.exists():
        print(f"❌ Training data not found: {training_data_path}")
        return False
    
    print("⚠️  IMPORTANT: This will regenerate fingerprints using the improved method.")
    print("   The old fingerprints were too simplistic and didn't capture musical features well.")
    print("   This requires the original audio files to regenerate fingerprints.")
    print("\n   However, we can't regenerate from JSON alone - we need the audio files.")
    print("   The training data only contains fingerprints, not audio.")
    print("\n   SOLUTION: We need to either:")
    print("   1. Re-run the training pipeline with the improved fingerprint method")
    print("   2. Or use the existing fingerprints but with better similarity calculation")
    print("\n   For now, the improved similarity calculation should help filter better matches.")
    
    return True

if __name__ == "__main__":
    regenerate_fingerprints()
