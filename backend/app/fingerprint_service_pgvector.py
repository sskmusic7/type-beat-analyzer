"""
Fingerprint Service using pgvector (PostgreSQL vector extension)
Stores fingerprints directly in PostgreSQL - no separate FAISS index needed
"""

import numpy as np
import librosa
import hashlib
import os
import logging
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import BYTEA
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

Base = declarative_base()


class FingerprintModel(Base):
    """SQLAlchemy model for fingerprints with pgvector"""
    __tablename__ = "fingerprints"
    
    id = Column(Integer, primary_key=True, index=True)
    audio_hash = Column(String(64), unique=True, index=True)
    artist = Column(String(255), index=True)
    title = Column(String(255))
    embedding = Column(BYTEA)  # Will store as vector type with pgvector
    upload_date = Column(DateTime)
    uploader_id = Column(String(255))


class FingerprintServicePGVector:
    """
    Fingerprint service using PostgreSQL + pgvector
    No local FAISS index - everything in database
    """
    
    def __init__(self):
        """Initialize with PostgreSQL connection"""
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/typebeat"
        )
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables and enable pgvector extension
        self._setup_database()
        
        self.embedding_dim = 128
    
    def _setup_database(self):
        """Create tables and enable pgvector extension"""
        try:
            # Enable pgvector extension
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create vector column if using pgvector (not BYTEA)
            # Check if vector column exists, if not, migrate
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'fingerprints' AND column_name = 'embedding'
                """))
                row = result.fetchone()
                
                if row and row[1] != 'USER-DEFINED':  # Not vector type yet
                    logger.info("Migrating embedding column to vector type...")
                    conn.execute(text("""
                        ALTER TABLE fingerprints 
                        DROP COLUMN IF EXISTS embedding;
                        ALTER TABLE fingerprints 
                        ADD COLUMN embedding vector(128);
                    """))
                    conn.commit()
                elif not row:
                    # Column doesn't exist, create it
                    conn.execute(text("""
                        ALTER TABLE fingerprints 
                        ADD COLUMN embedding vector(128);
                    """))
                    conn.commit()
            
            logger.info("Database setup complete with pgvector")
        except Exception as e:
            logger.warning(f"pgvector setup failed (may need to install extension): {e}")
            logger.info("Falling back to BYTEA storage - install pgvector for better performance")
    
    def _generate_fingerprint(self, audio_path: str) -> np.ndarray:
        """Generate 128-dim fingerprint (same as FAISS version)"""
        y, sr = librosa.load(
            audio_path,
            sr=8000,
            mono=True,
            duration=1.0
        )
        y = librosa.util.normalize(y)
        
        mel_spec = librosa.feature.melspectrogram(
            y=y, sr=sr, n_mels=256, fmin=300, fmax=4000,
            n_fft=1024, hop_length=256
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        mel_flat = mel_spec_db.flatten()
        
        if len(mel_flat) >= self.embedding_dim:
            embedding = mel_flat[:self.embedding_dim]
            if len(mel_flat) > self.embedding_dim:
                remaining = mel_flat[self.embedding_dim:]
                chunk_size = len(remaining) // (self.embedding_dim - 64)
                if chunk_size > 0:
                    pooled = [np.mean(remaining[i:i+chunk_size]) 
                             for i in range(0, len(remaining), chunk_size)]
                    embedding[64:] = pooled[:64]
        else:
            embedding = np.pad(mel_flat, (0, self.embedding_dim - len(mel_flat)), 'constant')
        
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding.astype(np.float32)
    
    def _compute_audio_hash(self, audio_path: str) -> str:
        """Compute SHA256 hash"""
        hasher = hashlib.sha256()
        with open(audio_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def add_fingerprint(self, audio_path: str, artist: str, 
                       title: Optional[str] = None, 
                       uploader_id: Optional[str] = None) -> int:
        """Add fingerprint to database"""
        try:
            embedding = self._generate_fingerprint(audio_path)
            audio_hash = self._compute_audio_hash(audio_path)
            
            db = self.SessionLocal()
            try:
                # Check if exists
                existing = db.query(FingerprintModel).filter(
                    FingerprintModel.audio_hash == audio_hash
                ).first()
                if existing:
                    logger.warning(f"Audio already in database: {audio_hash}")
                    return existing.id
                
                # Convert embedding to string format for pgvector
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                
                # Insert
                from datetime import datetime
                fingerprint = FingerprintModel(
                    audio_hash=audio_hash,
                    artist=artist,
                    title=title or os.path.basename(audio_path),
                    embedding=embedding_str,  # pgvector accepts string format
                    upload_date=datetime.now(),
                    uploader_id=uploader_id
                )
                db.add(fingerprint)
                db.commit()
                db.refresh(fingerprint)
                
                logger.info(f"Added fingerprint {fingerprint.id} for {artist}")
                return fingerprint.id
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error adding fingerprint: {e}", exc_info=True)
            raise
    
    def search_similar(self, audio_path: str, top_k: int = 5, 
                      threshold: float = 0.7) -> List[Dict]:
        """Search for similar beats using pgvector cosine similarity"""
        try:
            query_embedding = self._generate_fingerprint(audio_path)
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            db = self.SessionLocal()
            try:
                # Use pgvector cosine distance (1 - cosine similarity)
                # Lower distance = more similar
                results = db.execute(text("""
                    SELECT id, artist, title, audio_hash, upload_date, uploader_id,
                           1 - (embedding <=> :query_embedding::vector) as similarity,
                           (embedding <=> :query_embedding::vector) as distance
                    FROM fingerprints
                    WHERE 1 - (embedding <=> :query_embedding::vector) >= :threshold
                    ORDER BY embedding <=> :query_embedding::vector
                    LIMIT :top_k
                """), {
                    'query_embedding': embedding_str,
                    'threshold': threshold,
                    'top_k': top_k
                })
                
                matches = []
                for row in results:
                    matches.append({
                        'id': row[0],
                        'artist': row[1],
                        'title': row[2],
                        'audio_hash': row[3],
                        'upload_date': row[4].isoformat() if row[4] else None,
                        'uploader_id': row[5],
                        'similarity': float(row[5]),
                        'distance': float(row[6]),
                        'rank': len(matches) + 1
                    })
                
                logger.info(f"Found {len(matches)} similar beats")
                return matches
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error searching: {e}", exc_info=True)
            # Fallback to BYTEA if pgvector not available
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        db = self.SessionLocal()
        try:
            total = db.query(FingerprintModel).count()
            artists = db.execute(text("""
                SELECT COUNT(DISTINCT artist) FROM fingerprints
            """)).scalar()
            artist_list = db.execute(text("""
                SELECT DISTINCT artist FROM fingerprints ORDER BY artist
            """)).fetchall()
            
            return {
                'total_fingerprints': total,
                'artists': artists or 0,
                'artist_list': [row[0] for row in artist_list]
            }
        finally:
            db.close()
