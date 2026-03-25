"""
Demucs v4 Stem Separator for type beat analysis.

Separates audio into 4 stems: drums, bass, vocals, other (melody/synths).
Then extracts per-stem features to understand production composition.

CPU-only mode: ~3-5 min per track (acceptable for one-time training).
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import librosa


class StemSeparator:
    """
    Separate audio into stems using Demucs v4 (htdemucs model),
    then extract per-stem audio features.

    Lazy-loads the model on first use (~80MB download on first run).
    """

    def __init__(self, model_name: str = "htdemucs", device: str = "cpu"):
        """
        Args:
            model_name: Demucs model variant. 'htdemucs' is the default v4 model.
            device: 'cpu' or 'cuda'. Shadow PC has no GPU so default is cpu.
        """
        self.model_name = model_name
        self.device = device
        self._model = None

    def _ensure_model(self):
        """Lazy-load the Demucs model."""
        if self._model is not None:
            return

        import torch
        from demucs.pretrained import get_model

        print(f"[StemSeparator] Loading {self.model_name} model (device={self.device}) ...")
        self._model = get_model(self.model_name)
        self._model.to(torch.device(self.device))
        self._model.eval()
        print("[StemSeparator] Model loaded.")

    def separate(self, audio_path: str, output_dir: Optional[str] = None) -> Dict[str, np.ndarray]:
        """
        Separate audio into stems.

        Args:
            audio_path: Path to audio file.
            output_dir: If provided, save stems as WAV files here.

        Returns:
            Dict mapping stem name → numpy audio array (mono, 44100 Hz).
            Keys: 'drums', 'bass', 'vocals', 'other'
        """
        self._ensure_model()

        import torch
        from demucs.apply import apply_model
        from demucs.audio import AudioFile

        audio_path = str(Path(audio_path).resolve())

        # Load audio at model's sample rate
        sr = self._model.samplerate
        wav = AudioFile(audio_path).read(streams=0, samplerate=sr, channels=self._model.audio_channels)
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()
        wav = wav.unsqueeze(0).to(self.device)

        # Run separation
        print(f"[StemSeparator] Separating stems (CPU, this may take a few minutes) ...")
        with torch.no_grad():
            sources = apply_model(self._model, wav, device=self.device)

        # sources shape: (1, num_sources, channels, samples)
        sources = sources.squeeze(0)  # (num_sources, channels, samples)

        # Map to stem names
        stem_names = self._model.sources  # e.g. ['drums', 'bass', 'other', 'vocals']
        stems = {}
        for i, name in enumerate(stem_names):
            stem_audio = sources[i].mean(0).cpu().numpy()  # mono
            # Undo normalization
            stem_audio = stem_audio * ref.std().item() + ref.mean().item()
            stems[name] = stem_audio

        # Optionally save to disk
        if output_dir:
            import soundfile as sf
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            for name, audio in stems.items():
                sf.write(str(out / f"{name}.wav"), audio, sr)
            print(f"[StemSeparator] Stems saved to {out}")

        return stems

    def analyze_stems(self, audio_path: str) -> Dict[str, Any]:
        """
        Separate audio and extract per-stem features.

        Returns a dict with per-stem energy ratios, spectral profiles,
        and an overall stem mix breakdown.
        """
        stems = self.separate(audio_path)

        sr = self._model.samplerate
        total_energy = 0.0
        stem_data = {}

        for name, audio in stems.items():
            rms = np.sqrt(np.mean(audio ** 2))
            energy = float(rms ** 2)
            total_energy += energy

            # Spectral centroid for brightness characterization
            if rms > 1e-6:
                centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
                centroid_mean = float(centroid.mean())
            else:
                centroid_mean = 0.0

            stem_data[name] = {
                "rms": round(float(rms), 6),
                "energy": energy,
                "centroid_hz": round(centroid_mean, 1),
            }

        # Compute mix ratios
        if total_energy > 0:
            for name in stem_data:
                stem_data[name]["mix_ratio"] = round(stem_data[name]["energy"] / total_energy, 4)
        else:
            for name in stem_data:
                stem_data[name]["mix_ratio"] = 0.0

        # Clean up raw energy (not useful in output)
        for name in stem_data:
            del stem_data[name]["energy"]

        # Determine dominant stem
        dominant = max(stem_data, key=lambda s: stem_data[s]["mix_ratio"])

        return {
            "stems": stem_data,
            "dominant_stem": dominant,
            "has_vocals": stem_data.get("vocals", {}).get("mix_ratio", 0) > 0.05,
        }
