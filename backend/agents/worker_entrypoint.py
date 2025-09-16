# """
# LiveKit worker entrypoint for translation agents.
# """
# import asyncio
# import json
# import logging
# from dotenv import load_dotenv

# from livekit.agents import JobContext, WorkerOptions, cli
# from supabase import create_client

# from app.core.config import get_settings
# from app.db.v1.models import DatabaseService
# from app.services.livekit.room_manager import PatternBRoomManager
# from app.services.livekit.agent import LiveKitService
# from app.services.realtime.livekit_translation_agent import LiveKitTranslationService
# from app.services.realtime.audio_filter_agent import AudioFilteredTranslationService

# # Initialize services
# load_dotenv()
# settings = get_settings()
# supabase = create_client(settings.supabase_url, settings.supabase_service_role_key or settings.supabase_anon_key)
# db_service = DatabaseService(supabase)

# # Global instances
# room_manager = PatternBRoomManager(db_service)
# livekit_service = LiveKitService(room_manager)
# livekit_translation_service = LiveKitTranslationService()
# audio_filtered_service = AudioFilteredTranslationService()


# async def entrypoint(ctx: JobContext):
#     """
#     Main entrypoint for translation worker.
#     Each worker instance handles ONE user's translation needs.
#     """
#     participant_identity = None
    
#     try:
#         # Quick job acceptance to avoid timeout
#         logging.info(f"Agent job received for room: {ctx.room.name}")

#         # Extract user identity from job metadata (set during dispatch)
#         if ctx.job.metadata:
#             try:
#                 metadata = json.loads(ctx.job.metadata)
#                 participant_identity = metadata.get("user_identity")
#                 logging.info(f"Agent metadata: {metadata}")
#             except Exception as e:
#                 logging.warning(f"Failed to parse job metadata: {e}")
        
#         # Fallback to room participant if no metadata
#         if not participant_identity:
#             participant_identity = ctx.room.local_participant.identity
#             logging.warning("Using room participant identity as fallback")

#         logging.info(f"Starting translation worker for user: {participant_identity}")

#         # Determine if this should use real-time translation
#         use_realtime = True  # Re-enabled after fixing profile creation
#         room_type = "general"
        
#         # Check metadata for explicit configuration
#         if ctx.job.metadata:
#             try:
#                 metadata = json.loads(ctx.job.metadata)
#                 use_realtime = metadata.get("use_realtime", True)
#                 room_type = metadata.get("room_type", "general")
                
#                 logging.info(f"Room type: {room_type}, Use realtime: {use_realtime}")
#             except Exception as e:
#                 logging.warning(f"Error parsing metadata for realtime config: {e}")
        
#         # Create user profile from metadata
#         from app.models.domain.profiles import UserLanguageProfile, SupportedLanguage
        
#         # Extract user profile information from metadata
#         user_profile = None
#         if ctx.job.metadata:
#             try:
#                 metadata = json.loads(ctx.job.metadata)
                
#                 # Get native language
#                 native_language = SupportedLanguage(metadata.get("native_language", "en"))
                
#                 # Get default voice avatar for the language
#                 from app.models.domain.profiles import VOICE_AVATARS
#                 avatars = VOICE_AVATARS.get(native_language.value, VOICE_AVATARS["en"])
#                 default_avatar = avatars[0] if avatars else VOICE_AVATARS["en"][0]
                
#                 user_profile = UserLanguageProfile(
#                     user_identity=participant_identity,
#                     native_language=native_language,
#                     preferred_voice_avatar=default_avatar,
#                     translation_preferences=metadata.get("translation_preferences", {
#                         "formal_tone": False,
#                         "preserve_emotion": True
#                     })
#                 )
#             except Exception as e:
#                 logging.warning(f"Error creating user profile from metadata: {e}")
        
#         # Fallback user profile
#         if not user_profile:
#             # Get default voice avatar for English
#             from app.models.domain.profiles import VOICE_AVATARS
#             default_avatar = VOICE_AVATARS["en"][0]
            
#             user_profile = UserLanguageProfile(
#                 user_identity=participant_identity,
#                 native_language=SupportedLanguage.ENGLISH,
#                 preferred_voice_avatar=default_avatar,
#                 translation_preferences={
#                     "formal_tone": False,
#                     "preserve_emotion": True
#                 }
#             )

#         # Determine if this is a multi-user translation room
#         room_participant_count = len(ctx.room.remote_participants) + 1  # +1 for local participant
#         is_translation_room = room_participant_count <= 3  # 2 users + potential agents
        
#         logging.info(f"🏠 ROOM ANALYSIS: {ctx.room.name}")
#         logging.info(f"   - Participant count: {room_participant_count}")
#         logging.info(f"   - Remote participants: {[p.identity for p in ctx.room.remote_participants.values()]}")
#         logging.info(f"   - Is translation room: {is_translation_room}")
#         logging.info(f"   - Agent will be: {'AudioFiltered' if is_translation_room else 'Standard'}")
        
#         # Create and start the appropriate translation agent
#         try:
#             if is_translation_room:
#                 # Use audio-filtered agent for multi-user translation
#                 agent = await audio_filtered_service.create_agent(user_profile)
#                 await audio_filtered_service.start_agent(participant_identity, ctx)
#                 logging.info(f"Audio-filtered translation agent started for {participant_identity}")
#             else:
#                 # Use standard agent for single-user voice assistant
#                 agent = await livekit_translation_service.create_agent(user_profile)
#                 await livekit_translation_service.start_agent(participant_identity, ctx)
#                 logging.info(f"Standard translation agent started for {participant_identity}")

#             # Keep the agent running - the agent handles all the processing
#             await asyncio.sleep(float('inf'))

#         except asyncio.TimeoutError:
#             logging.error(f"Agent creation timed out for {participant_identity}")
#             raise
#         except Exception as e:
#             logging.error(f"Error creating translation agent for {participant_identity}: {e}")
#             raise

#     except asyncio.CancelledError:
#         logging.info(f"Translation worker for {participant_identity} cancelled")
#     except Exception as e:
#         logging.error(f"Error in translation worker for {participant_identity}: {e}")
#         # Don't re-raise to avoid worker crash
#     finally:
#         # Cleanup
#         if participant_identity:
#             try:
#                 # Cleanup LiveKit translation service
#                 await livekit_translation_service.stop_agent(participant_identity)
#                 logging.info(f"Cleaned up LiveKit translation agent for {participant_identity}")
                    
#             except Exception as e:
#                 logging.error(f"Error during cleanup for {participant_identity}: {e}")


# if __name__ == "__main__":
#     # Configure logging
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )

#     # Run the LiveKit Agents worker with explicit dispatch
#     cli.run_app(
#         WorkerOptions(
#             entrypoint_fnc=entrypoint,
#             # Use explicit agent dispatch with a named agent
#             # agent_name="translation-agent",
#         )
#     )
