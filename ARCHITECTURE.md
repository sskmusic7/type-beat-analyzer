# Type Beat Analyzer - Architecture & Model Explanation

## Current System Architecture

### ⚠️ **IMPORTANT: No Trained ML Model Yet**

The system is currently using a **rule-based feature classifier**, NOT a trained neural network.

---

## How It Works Right Now

### 1. **Audio Feature Extraction** (`audio_processor.py`)
Uses `librosa` to extract:
- **Tempo (BPM)** - Beat per minute
- **Musical Key** - C, C#, D, etc.
- **Spectral Centroid** - Brightness of sound (Hz)
- **MFCC** - Mel-frequency cepstral coefficients (timbre)
- **Chroma** - Harmonic content
- **Mel-spectrogram** - Frequency representation

### 2. **Feature-Based Classifier** (`feature_based_classifier.py`)
**This is what's currently powering predictions:**

- **Rule-based scoring system** (NOT machine learning)
- Scores your beat against genre profiles:
  - Trap: 65-85 BPM, darker keys, 1000-3000 Hz spectral
  - Drill: 60-75 BPM, specific keys
  - R&B: 70-100 BPM, brighter spectral
  - Pop: 100-140 BPM, high spectral
  - EDM: 120-140 BPM, very bright
  - Rock: 100-140 BPM
  - Alternative: 80-120 BPM

- **Scoring Algorithm:**
  1. Tempo match (0-40 points)
  2. Key match (0-20 points)
  3. Spectral centroid match (0-30 points)
  4. MFCC variance (0-10 points)
  
- Returns top 5 artists from matching genres

### 3. **Model Inference** (`model_inference.py`)
- **Tries to load trained PyTorch model** from `data/models/type_beat_classifier.pt`
- **Currently: Model doesn't exist** (directory is empty)
- **Falls back to:** `FeatureBasedClassifier` (rule-based)

---

## What SHOULD Be Powering It

### Trained CNN Model (`ml/train_model.py`)

**Architecture:**
- **Input:** Mel-spectrograms (128 bins × time frames)
- **Model:** Convolutional Neural Network (CNN)
  - 3 Conv layers + BatchNorm + ReLU
  - MaxPooling
  - Fully connected layers
  - Output: Artist probabilities

**Training Process:**
1. Load audio files from `data/raw/{artist_name}/`
2. Extract mel-spectrograms (30s clips)
3. Data augmentation (pitch shift, time stretch)
4. Train/validation split (80/20)
5. Save model to `data/models/type_beat_classifier.pt`

**Status:** ❌ **NOT TRAINED YET** - Training script exists but hasn't been run

---

## Data Flow

```
User Uploads Beat
    ↓
AudioProcessor.extract_features()
    ↓
Extracts: tempo, key, spectral, MFCC, mel-spectrogram
    ↓
ModelInference.predict()
    ↓
Checks: Does trained model exist? (NO)
    ↓
Falls back to: FeatureBasedClassifier.classify()
    ↓
Scores against genre profiles (rule-based)
    ↓
Returns: Top 5 artists with confidence scores
```

---

## To Train a Real Model

### Step 1: Prepare Data
```bash
# Organize audio files:
data/raw/
  ├── drake/
  │   ├── beat1.wav
  │   ├── beat2.wav
  │   └── ...
  ├── travis_scott/
  │   └── ...
  └── ...
```

### Step 2: Train Model
```bash
cd ml
python train_model.py \
  --data_dir ../data/raw \
  --artists "Drake,Travis Scott,Metro Boomin" \
  --epochs 50 \
  --batch_size 32
```

### Step 3: Enable Model Loading
Uncomment line 32 in `backend/app/model_inference.py`:
```python
self._load_model()  # Remove the # comment
```

---

## Current Limitations

1. **Rule-based, not learned** - Uses hardcoded genre profiles
2. **Limited accuracy** - Can't learn complex patterns
3. **No artist-specific features** - Only genre-level matching
4. **Fixed thresholds** - Doesn't adapt to data

---

## Why This Exists

The feature-based classifier was created as a **working MVP** while:
- Waiting for training data collection
- Testing the audio processing pipeline
- Providing immediate functionality

**Next Step:** Train the CNN model with real type beat data for accurate artist classification.
