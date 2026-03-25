"""
CLAP Zero-Shot Text-Prompt Scorer for type beat analysis.

Uses Microsoft CLAP (Contrastive Language-Audio Pretraining) to score
audio files against curated text prompts describing instruments, moods,
tempo, and production styles common in type beats.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import librosa
import torch
import numpy as np

# Curated text prompts for type beat analysis.
# CLAP works best with natural-language descriptions, so prompts are
# phrased as descriptive sentences rather than bare keywords.
TYPE_BEAT_PROMPTS: List[str] = [
    # --- Instruments ---
    "808 bass with heavy sub frequencies",
    "crisp hi-hat patterns",
    "open hi-hat rolls",
    "piano melody",
    "acoustic guitar",
    "electric guitar with distortion",
    "synthesizer lead melody",
    "synth pad atmosphere",
    "orchestral strings",
    "flute melody",
    "bell sounds and chimes",
    "choir and vocal chops",
    "brass horns",
    "plucked harp or kalimba",
    "acoustic drum kit",
    "finger snaps and claps",
    "vinyl crackle and texture",
    "sound effects and risers",
    # --- Moods ---
    "dark and ominous mood",
    "aggressive and hard-hitting energy",
    "melodic and emotional feel",
    "chill and relaxed vibes",
    "hype and energetic mood",
    "ethereal and dreamy atmosphere",
    "sad and melancholic tone",
    "uplifting and triumphant feel",
    "mysterious and suspenseful mood",
    "playful and bouncy energy",
    # --- Genre / Style ---
    "trap beat with rolling hi-hats",
    "boom bap with chopped samples",
    "drill beat with sliding 808s",
    "lo-fi hip hop with warm textures",
    "R&B smooth instrumental",
    "afrobeat rhythmic percussion",
    "jersey club with fast kicks",
    "rage beat with distorted synths",
    "pluggnb melodic beat",
    "soul sample with vinyl warmth",
    # --- Tempo / Rhythm ---
    "slow tempo beat",
    "mid-tempo groove",
    "fast tempo beat",
    "bouncy rhythmic pattern",
    "half-time drum pattern",
    "triplet hi-hat flow",
    # --- Production Qualities ---
    "minimalist sparse production",
    "layered and dense arrangement",
    "distorted and saturated sound",
    "clean and polished mix",
    "heavy reverb and spacious",
    "lo-fi dusty texture",
    "punchy and compressed drums",
    "wide stereo image",
]


class CLAPScorer:
    """
    Zero-shot audio tagger using Microsoft CLAP.

    Lazily loads the ~600MB CLAP 2023 model on first use.
    Model weights are cached to ``models/clap/`` under the base directory.
    """

    def __init__(
        self,
        prompts: Optional[List[str]] = None,
        model_dir: Optional[str] = None,
    ):
        """
        Args:
            prompts: Custom list of text prompts. Defaults to TYPE_BEAT_PROMPTS.
            model_dir: Directory to cache the CLAP model weights.
                        Defaults to ``<script_dir>/../models/clap/``.
        """
        self.prompts = prompts or TYPE_BEAT_PROMPTS

        if model_dir is None:
            base = Path(__file__).resolve().parent.parent
            self.model_dir = base / "models" / "clap"
        else:
            self.model_dir = Path(model_dir)

        # Lazy-loaded
        self._clap = None
        self._text_embeddings = None

    def _ensure_model(self) -> None:
        """Load the CLAP model and pre-compute text embeddings (once)."""
        if self._clap is not None:
            return

        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Point HuggingFace cache into our model dir so weights land there.
        os.environ["HF_HOME"] = str(self.model_dir)

        print(f"[CLAPScorer] Loading CLAP model (cache: {self.model_dir}) ...")
        print("[CLAPScorer] First run will download ~600 MB of weights.")
        sys.stdout.flush()

        from msclap import CLAP

        self._clap = CLAP(version="2023", use_cuda=False)

        # Patch read_audio to use librosa instead of torchaudio.
        # torchaudio >=2.10 requires torchcodec + FFmpeg DLLs on Windows,
        # whereas librosa handles WAV/MP3 out of the box via soundfile/audioread.
        def _librosa_read_audio(audio_path, resample=True):
            sr_target = self._clap.args.sampling_rate
            y, sr = librosa.load(audio_path, sr=sr_target if resample else None, mono=True)
            return torch.from_numpy(y).unsqueeze(0).float(), sr_target if resample else sr

        self._clap.read_audio = _librosa_read_audio

        print(f"[CLAPScorer] Model loaded. Pre-computing embeddings for {len(self.prompts)} prompts ...")
        sys.stdout.flush()

        # Pre-compute text embeddings so we only do it once.
        self._text_embeddings = self._clap.get_text_embeddings(self.prompts)
        print("[CLAPScorer] Ready.")

    def score_audio(self, audio_path: str) -> Dict[str, float]:
        """
        Score an audio file against all text prompts.

        Args:
            audio_path: Path to a WAV or MP3 file.

        Returns:
            Dict mapping each prompt string to a similarity score in [0, 1].
        """
        self._ensure_model()

        audio_path = str(Path(audio_path).resolve())
        audio_emb = self._clap.get_audio_embeddings([audio_path])
        similarity = self._clap.compute_similarity(audio_emb, self._text_embeddings)

        # similarity shape: (1, num_prompts) — squeeze to 1-D
        scores = similarity.squeeze(0).detach()

        # Normalize to [0, 1]: compute raw cosine similarity (undo logit scaling)
        # then shift to [0, 1] range via (cos_sim + 1) / 2.
        logit_scale = self._clap.clap.logit_scale.exp().detach()
        cosine_sim = scores / logit_scale  # back to [-1, 1]
        probs = ((cosine_sim + 1.0) / 2.0).cpu().numpy()

        return {prompt: float(prob) for prompt, prob in zip(self.prompts, probs)}

    def top_tags(
        self, audio_path: str, n: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Return the top *n* scoring prompts for an audio file.

        Args:
            audio_path: Path to a WAV or MP3 file.
            n: Number of top tags to return.

        Returns:
            List of (prompt, score) tuples sorted by score descending.
        """
        scores = self.score_audio(audio_path)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[:n]
