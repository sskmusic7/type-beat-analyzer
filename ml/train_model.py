"""
Training pipeline for type beat classification model
Based on research: CNN with mel-spectrograms, data augmentation
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import librosa
from pathlib import Path
import json
import logging
from typing import List, Dict, Tuple
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TypeBeatDataset(Dataset):
    """
    Dataset for type beat classification
    Loads audio files and extracts mel-spectrograms
    """
    
    def __init__(
        self,
        data_dir: str,
        artist_list: List[str],
        sample_rate: int = 22050,
        duration: int = 30,
        augment: bool = True
    ):
        self.data_dir = Path(data_dir)
        self.artist_list = artist_list
        self.artist_to_idx = {artist: idx for idx, artist in enumerate(artist_list)}
        self.sample_rate = sample_rate
        self.duration = duration
        self.augment = augment
        
        # Load file paths
        self.samples = []
        for artist in artist_list:
            artist_dir = self.data_dir / artist.lower().replace(" ", "_")
            if artist_dir.exists():
                for audio_file in artist_dir.glob("*.wav"):
                    self.samples.append((str(audio_file), artist))
        
        logger.info(f"Loaded {len(self.samples)} samples across {len(artist_list)} artists")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        audio_path, artist = self.samples[idx]
        
        # Load and preprocess audio
        y, sr = librosa.load(
            audio_path,
            sr=self.sample_rate,
            mono=True,
            duration=self.duration
        )
        
        # Normalize (CRITICAL per research)
        y = librosa.util.normalize(y)
        
        # Data augmentation (from Neural Audio FP paper)
        if self.augment:
            y = self._augment_audio(y)
        
        # Extract mel-spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=y,
            sr=sr,
            n_mels=128,
            fmax=8000
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # Normalize to [0, 1]
        mel_spec_db = (mel_spec_db - mel_spec_db.min()) / (mel_spec_db.max() - mel_spec_db.min() + 1e-8)
        
        # Convert to tensor: (1, 128, time_frames)
        mel_spec_tensor = torch.from_numpy(mel_spec_db).float().unsqueeze(0)
        
        # Label
        label = self.artist_to_idx[artist]
        
        return mel_spec_tensor, label
    
    def _augment_audio(self, y: np.ndarray) -> np.ndarray:
        """
        Apply data augmentation (from research papers)
        - Time stretching (93-107%)
        - Pitch shifting (±2 semitones)
        - Background noise (5-15 dB SNR)
        """
        # Time stretching
        if np.random.random() > 0.5:
            rate = np.random.uniform(0.93, 1.07)
            y = librosa.effects.time_stretch(y, rate=rate)
        
        # Pitch shifting
        if np.random.random() > 0.5:
            n_steps = np.random.randint(-2, 3)
            y = librosa.effects.pitch_shift(y, sr=self.sample_rate, n_steps=n_steps)
        
        # Background noise (simplified - would use actual noise samples)
        if np.random.random() > 0.7:
            noise = np.random.normal(0, 0.01, len(y))
            snr_db = np.random.uniform(5, 15)
            signal_power = np.mean(y ** 2)
            noise_power = signal_power / (10 ** (snr_db / 10))
            noise = noise * np.sqrt(noise_power / np.mean(noise ** 2))
            y = y + noise
        
        return y


class TypeBeatClassifier(nn.Module):
    """
    CNN model for type beat classification
    Architecture based on genre classification research (75-80% accuracy)
    """
    
    def __init__(self, num_classes: int):
        super(TypeBeatClassifier, self).__init__()
        
        # CNN layers
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        
        self.conv4 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)
        )
        
        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        
        # Classifier
        self.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x


def train(
    data_dir: str,
    artist_list: List[str],
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    model_save_path: str = "data/models/type_beat_classifier.pt"
):
    """
    Train the type beat classifier
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    # Create datasets
    dataset = TypeBeatDataset(data_dir, artist_list, augment=True)
    
    # Split train/val (80/20)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Initialize model
    model = TypeBeatClassifier(num_classes=len(artist_list)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_val_acc = 0.0
    
    # Training loop
    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
        
        train_acc = 100 * train_correct / train_total
        
        # Validate
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
        
        val_acc = 100 * val_correct / val_total
        scheduler.step(val_loss)
        
        logger.info(
            f"Epoch {epoch+1}/{epochs} - "
            f"Train Loss: {train_loss/len(train_loader):.4f}, Train Acc: {train_acc:.2f}% - "
            f"Val Loss: {val_loss/len(val_loader):.4f}, Val Acc: {val_acc:.2f}%"
        )
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'model': model.state_dict(),
                'artist_list': artist_list,
                'epoch': epoch,
                'val_acc': val_acc
            }, model_save_path)
            logger.info(f"Saved best model with val_acc: {val_acc:.2f}%")
    
    logger.info(f"Training complete! Best validation accuracy: {best_val_acc:.2f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train type beat classifier")
    parser.add_argument("--data_dir", type=str, default="data/raw", help="Directory with artist subdirectories")
    parser.add_argument("--artists", nargs="+", default=["Drake", "Travis Scott", "Metro Boomin"],
                       help="List of artists to train on")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--model_path", type=str, default="data/models/type_beat_classifier.pt",
                       help="Path to save model")
    
    args = parser.parse_args()
    
    train(
        data_dir=args.data_dir,
        artist_list=args.artists,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        model_save_path=args.model_path
    )
