"""
Processing monitor for tracking audio analysis jobs
"""

from typing import Dict, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class ProcessingMonitor:
    """
    Tracks processing status for audio analysis jobs
    """
    
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
    
    def create_job(self, filename: str) -> str:
        """Create a new processing job and return job ID"""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            "job_id": job_id,
            "filename": filename,
            "status": "queued",
            "progress": 0,
            "stage": "Initializing",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "results": None
        }
        logger.info(f"Created job {job_id} for {filename}")
        return job_id
    
    def update_job(self, job_id: str, **kwargs):
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)
            if 'status' in kwargs:
                logger.info(f"Job {job_id} status: {kwargs['status']}")
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job status"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self, limit: int = 10) -> list:
        """Get recent jobs"""
        sorted_jobs = sorted(
            self.jobs.values(),
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        return sorted_jobs[:limit]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Remove jobs older than max_age_hours"""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = [
            job_id for job_id, job in self.jobs.items()
            if datetime.fromisoformat(job['created_at']) < cutoff
        ]
        
        for job_id in to_remove:
            del self.jobs[job_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")
