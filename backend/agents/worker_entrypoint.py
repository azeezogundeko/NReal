"""
LiveKit worker entrypoint for translation agents.
"""
import asyncio
import logging

from livekit.agents import JobContext, WorkerOptions, cli

from app.services.livekit.room_manager import PatternBRoomManager
from app.services.livekit.agent import LiveKitService


# Global instances
room_manager = PatternBRoomManager()
livekit_service = LiveKitService(room_manager)


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for translation worker.
    Each worker instance handles ONE user's translation needs.
    """

    # Extract user identity from room or job metadata
    participant_identity = ctx.room.local_participant.identity

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

    # Run the LiveKit Agents worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Each user gets their own worker process
            agent_dispatch=True,
        )
    )
