"""
LiveKit worker entrypoint for translation agents.
"""
import asyncio
import json
import logging
from dotenv import load_dotenv

from livekit.agents import JobContext, WorkerOptions, cli
from supabase import create_client

from app.core.config import get_settings
from app.db.models import DatabaseService
from app.services.livekit.room_manager import PatternBRoomManager
from app.services.livekit.agent import LiveKitService

# Initialize services
load_dotenv()
settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_service_role_key or settings.supabase_anon_key)
db_service = DatabaseService(supabase)

# Global instances
room_manager = PatternBRoomManager(db_service)
livekit_service = LiveKitService(room_manager)


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for translation worker.
    Each worker instance handles ONE user's translation needs.
    """

    # Extract user identity from job metadata (set during dispatch)
    participant_identity = None
    if ctx.job.metadata:
        try:
            metadata = json.loads(ctx.job.metadata)
            participant_identity = metadata.get("user_identity")
            logging.info(f"Agent metadata: {metadata}")
        except Exception as e:
            logging.warning(f"Failed to parse job metadata: {e}")
    
    # Fallback to room participant if no metadata
    if not participant_identity:
        participant_identity = ctx.room.local_participant.identity
        logging.warning("Using room participant identity as fallback")

    logging.info(f"Starting translation worker for user: {participant_identity}")
    logging.info(f"Room: {ctx.room.name}")

    try:
        # Create and start the user's translation agent
        agent = await livekit_service.create_user_agent(participant_identity, ctx)

        # Keep the agent running - the AgentSession handles all the processing
        await asyncio.sleep(float('inf'))

    except asyncio.CancelledError:
        logging.info(f"Translation worker for {participant_identity} cancelled")
    except Exception as e:
        logging.error(f"Error in translation worker for {participant_identity}: {e}")
        raise
    finally:
        # Cleanup
        livekit_service.remove_user_agent(participant_identity)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run the LiveKit Agents worker with explicit dispatch
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Use explicit agent dispatch with a named agent
            agent_name="translation-agent",
        )
    )
