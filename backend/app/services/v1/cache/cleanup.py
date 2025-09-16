"""
Background task for cache cleanup and maintenance.
"""
import asyncio
import logging
from typing import Optional
from app.services.v1.livekit.room_manager import PatternBRoomManager


class CacheCleanupService:
    """Background service for cleaning up expired cache entries."""
    
    def __init__(self, room_manager: PatternBRoomManager, cleanup_interval_seconds: int = 600):
        """
        Initialize cache cleanup service.
        
        Args:
            room_manager: Room manager with cache to clean
            cleanup_interval_seconds: How often to run cleanup (default: 10 minutes)
        """
        self.room_manager = room_manager
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """Start the background cleanup task."""
        if self._running:
            logging.warning("Cache cleanup service is already running")
            return
            
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logging.info(f"Started cache cleanup service (interval: {self.cleanup_interval_seconds}s)")
        
    async def stop(self):
        """Stop the background cleanup task."""
        if not self._running:
            return
            
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        logging.info("Stopped cache cleanup service")
        
    async def _cleanup_loop(self):
        """Main cleanup loop that runs periodically."""
        try:
            while self._running:
                await self._perform_cleanup()
                await asyncio.sleep(self.cleanup_interval_seconds)
        except asyncio.CancelledError:
            logging.info("Cache cleanup loop cancelled")
            raise
        except Exception as e:
            logging.error(f"Error in cache cleanup loop: {e}")
            
    async def _perform_cleanup(self):
        """Perform cache cleanup and log statistics."""
        try:
            # Get stats before cleanup
            before_stats = self.room_manager.get_cache_stats()
            
            # Perform cleanup
            self.room_manager._cleanup_expired_cache()
            
            # Get stats after cleanup
            after_stats = self.room_manager.get_cache_stats()
            
            # Log cleanup results
            cleaned_count = before_stats["total_entries"] - after_stats["total_entries"]
            if cleaned_count > 0:
                logging.info(f"Cache cleanup: removed {cleaned_count} expired entries, "
                           f"{after_stats['active_entries']} active entries remaining")
            else:
                logging.debug(f"Cache cleanup: no expired entries, "
                            f"{after_stats['active_entries']} active entries")
                            
        except Exception as e:
            logging.error(f"Error during cache cleanup: {e}")


# Global cleanup service instance
_cleanup_service: Optional[CacheCleanupService] = None


async def start_cache_cleanup_service(room_manager: PatternBRoomManager):
    """Start the global cache cleanup service."""
    global _cleanup_service
    
    if _cleanup_service is None:
        _cleanup_service = CacheCleanupService(room_manager)
        await _cleanup_service.start()
    else:
        logging.warning("Cache cleanup service already initialized")


async def stop_cache_cleanup_service():
    """Stop the global cache cleanup service."""
    global _cleanup_service
    
    if _cleanup_service:
        await _cleanup_service.stop()
        _cleanup_service = None


def get_cache_cleanup_service() -> Optional[CacheCleanupService]:
    """Get the global cache cleanup service instance."""
    return _cleanup_service
