"""
Training service for fingerprint generation
Sends training requests to Shadow PC webhook server
Shadow PC handles YouTube downloads and uploads to Cloud Storage
"""

import os
import httpx
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ShadowPCTrainingService:
    """
    Training service that sends requests to Shadow PC
    Shadow PC runs actual training (YouTube works there!)
    """

    def __init__(self):
        """Initialize Shadow PC webhook client"""
        self.shadow_pc_url = os.getenv(
            "SHADOW_PC_WEBHOOK_URL",
            "http://46.247.137.210:8000"  # Default Shadow PC IP
        )
        self.timeout = 30  # HTTP timeout

        logger.info(f"🔗 Shadow PC Training Service initialized")
        logger.info(f"   Webhook URL: {self.shadow_pc_url}")

    async def check_shadow_pc_health(self) -> bool:
        """Check if Shadow PC webhook server is running"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.shadow_pc_url}/health")
                if response.status_code == 200:
                    logger.info("✅ Shadow PC webhook server is reachable")
                    return True
                else:
                    logger.warning(f"⚠️  Shadow PC returned status {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Cannot reach Shadow PC: {e}")
            return False

    async def start_training(
        self,
        artists: List[str],
        max_per_artist: int = 5,
        clear_existing: bool = False
    ) -> Dict:
        """
        Send training request to Shadow PC

        Args:
            artists: List of artist names to train on
            max_per_artist: Maximum tracks per artist
            clear_existing: Whether to clear existing fingerprints

        Returns:
            Response from Shadow PC
        """
        try:
            # Prepare request payload
            payload = {
                "artists": artists,
                "max_per_artist": max_per_artist,
                "clear_existing": clear_existing
            }

            logger.info(f"📤 Sending training request to Shadow PC")
            logger.info(f"   Artists: {', '.join(artists)}")
            logger.info(f"   Max per artist: {max_per_artist}")

            # Send request to Shadow PC
            async with httpx.AsyncClient(timeout=120) as client:  # 2 minute timeout
                response = await client.post(
                    f"{self.shadow_pc_url}/train/start",
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ Shadow PC accepted training request")
                    logger.info(f"   Message: {result.get('message')}")
                    return {
                        "success": True,
                        "message": "Training started on Shadow PC",
                        "shadow_pc_response": result
                    }
                elif response.status_code == 400:
                    error_detail = response.json().get('detail', 'Unknown error')
                    logger.warning(f"⚠️  Shadow PC busy: {error_detail}")
                    return {
                        "success": False,
                        "message": f"Shadow PC is busy: {error_detail}"
                    }
                else:
                    logger.error(f"❌ Shadow PC returned error {response.status_code}")
                    return {
                        "success": False,
                        "message": f"Shadow PC error: {response.status_code}"
                    }

        except httpx.ConnectError:
            logger.error(f"❌ Cannot connect to Shadow PC at {self.shadow_pc_url}")
            return {
                "success": False,
                "message": f"Cannot reach Shadow PC. Check if webhook server is running."
            }
        except Exception as e:
            logger.error(f"❌ Error sending training request: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

    async def get_training_status(self) -> Dict:
        """Get training status from Shadow PC"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.shadow_pc_url}/train/status")

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "is_training": False,
                        "message": "Cannot reach Shadow PC"
                    }
        except Exception as e:
            logger.error(f"❌ Error getting status from Shadow PC: {e}")
            return {
                "is_training": False,
                "message": f"Error: {str(e)}"
            }

    async def stop_training(self) -> Dict:
        """Stop training on Shadow PC"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.shadow_pc_url}/train/stop")

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "message": "Failed to stop training"
                    }
        except Exception as e:
            logger.error(f"❌ Error stopping training: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }


# Singleton instance
shadow_pc_service = ShadowPCTrainingService()
