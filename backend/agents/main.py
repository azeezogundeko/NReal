import os
import ast
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any

import dotenv
from livekit.agents import JobContext, AgentSession, WorkerOptions, WorkerType, cli
from livekit.plugins import silero, openai, deepgram, cartesia, groq
from livekit.plugins import spitch

from .dispatcher.dispatcher_agent import dispatcher
from .provider.config import provider_config_manager

from app.core.livekit_import import (
    SILERO_AVAILABLE, PLUGINS_AVAILABLE, GROQ_AVAILABLE, elevenlabs
)

# --- Load env & logging ---
dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------

def parse_metadata(ctx: JobContext) -> dict:
    """
    Extract and parse metadata from a JobContext.
    Supports JSON and Python dict string formats.
    """
    metadata = ctx.job.metadata  # ✅ pull out the actual metadata string

    if metadata is None:
        return {}

    if not isinstance(metadata, str):
        logging.warning(f"Metadata is not a string: {type(metadata)}")
        return {}

    try:
        # Try JSON first
        return json.loads(metadata)
    except json.JSONDecodeError:
        try:
            # Fallback: safely evaluate Python dict string
            return ast.literal_eval(metadata)
        except Exception as e:
            logging.warning(f"Failed to parse metadata: {e}")
            return {}

def identify_call_and_tenant(metadata: Dict[str, Any]) -> Tuple[str, bool]:
    """Determines if the session is a phone call and resolves the tenant ID."""
    is_phone_call = "sip_from" in metadata or "sip_to" in metadata
    if is_phone_call:
        caller, called_number = metadata.get("sip_from"), metadata.get("sip_to")
        logger.info(f"📞 Phone call: from={caller} to={called_number}")
        tenant_id = dispatcher.resolve_tenant_from_number(called_number)
    else:
        logger.info("🌐 WebRTC session detected")
        tenant_id = metadata.get("tenant_id", "default")
    return tenant_id, is_phone_call

# async def initialize_services(tenant_id: str) -> Tuple[BusinessLogicOrchestrator, AnalyticsReportingService, CreditAccount]:
#     """Initializes and sets up per-session services like credit and analytics."""
#     credit_service = CreditManagementDatabaseService()
#     await credit_service.initialize()

#     # Get user account from database

#     account = await credit_service.get_account_by_tenant(tenant_id)
#     credit_service.register_account(account)

#     orchestrator = BusinessLogicOrchestrator()
#     await orchestrator.initialize()
#     analytics_service = AnalyticsReportingService(orchestrator)
    
#     return orchestrator, analytics_service, sample_account

async def load_agent_and_llm(ctx: JobContext, metadata: Dict, tenant_id: str, agent_definition) -> Tuple[Any, Any]:
    """Loads the specific agent instance and the appropriate LLM client."""
    agent_name = ctx.job.agent_name
    agent = await dispatcher.loader.get_agent_instance(
        metadata.get("agent_type"), tenant_id, agent_name, ctx, agent_definition
    )
    llm_client = groq.LLM() if GROQ_AVAILABLE else openai.LLM(model="gpt-4", temperature=0.7)

    await agent.initialize_components(
        llm_client,
        global_llm_config=None,
        global_voice_config=None,
        global_transcriber_config=None,
        global_variables=None,
    )
    return agent, llm_client

async def setup_agent_session(llm_client) -> AgentSession:
    """Configures and returns the main AgentSession."""
    vad_component = await asyncio.to_thread(silero.VAD.load) if SILERO_AVAILABLE else None
    stt_client = provider_config_manager.get_stt_client() or deepgram.STT()
    # tts_client = provider_config_manager.get_tts_client() or deepgram.TTS()
    # tts_client = elevenlabs.TTS(voice_id="9Dbo4hEvXQ5l7MXGZFQA", model="eleven_multilingual_v2")
    tts_client = spitch.TTS(language="en", voice="kani")

    return AgentSession(stt=stt_client, llm=llm_client, tts=tts_client, vad=vad_component, preemptive_generation=True)

def register_event_handlers(session: AgentSession, agent, llm_client):
    """Defines and attaches event handlers to the agent session."""
    @session.on("user_speech_committed")
    def on_user_speech(ev):
        logger.info(f"User said: {ev.user_transcript}")
        async def process():
            try:
                response = await agent.process_workflow_message(ev.user_transcript, llm_client)
                if response:
                    await session.say(response)
                    logger.info(f"Agent responded: {response[:100]}...")
            except Exception as e:
                logger.error(f"Speech processing error: {e}")
                await session.say("I’m having trouble processing that right now.")
        asyncio.create_task(process())

    @session.on("agent_state_changed")
    def on_agent_state_changed(ev):
        logger.info("Agent state changed")

async def start_session_and_greet(session: AgentSession, agent, ctx: JobContext):
    """Starts the session and sends the appropriate initial greeting."""
    await session.start(agent=agent, room=ctx.room)
    try:
        # if is_phone_call:
        #     await session.generate_reply("Greet the caller and offer assistance.")
        #     logger.info("📞 Greeting sent")
        # else:
        initial_message = await agent.get_initial_message()
        if initial_message:
            await session.say(initial_message)
            logger.info(f"🌐 Initial message: {initial_message}")
    except Exception as e:
        logger.error(f"Failed to send initial message: {e}")

async def handle_session_end(session: AgentSession, session_id: str, account_id: str, orchestrator, analytics_service):
    """Waits for the session to end and performs cleanup and reporting tasks."""
    try:
        await session.wait_for_session_end()
    except Exception as e:
        logger.error(f"Session ended with error: {e}")
    finally:
        await metrics_collector.stop_collection(session_id)

        # Log summaries
        logger.info(f"Payment summary: {metrics_collector.get_usage_summary(session_id)}")
        final_balance = orchestrator.get_account_status(account_id).get('credit_status', {}).get('balance', 0)
        logger.info(f"Final balance: ${final_balance}")

        # Generate analytics
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=1)
            session_analytics = await analytics_service.generate_payg_analytics(account_id, "custom", start_date, end_date)
            logger.info(f"Analytics: {len(session_analytics.optimization_recommendations)} recommendations")
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}")


# -------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------
async def entrypoint(ctx: JobContext):
    """Main entry point for LiveKit agent runtime"""
    logger.info("🚀 Starting Qualification Agent")
    await ctx.connect()

    # --- Setup and Initialization ---
    metadata = parse_metadata(ctx)
    tenant_id, is_phone_call = identify_call_and_tenant(metadata)
    # agent_definition = dispatcher.get_agent_definition(tenant_id, ctx.job.agent_name)
    # orchestrator, analytics_service, sample_account = await initialize_services(tenant_id)
    agent, llm_client = await load_agent_and_llm(ctx, metadata, tenant_id)
    
    # --- Build session context ---
    session_id = f"{tenant_id}_{ctx.job.agent_name}_{int(asyncio.get_event_loop().time())}"
    # account_id = sample_account.account_id
    user_id = f"user_{tenant_id}"

    # --- Configure and start session ---
    session = await setup_agent_session(llm_client)
    register_event_handlers(session, agent, llm_client)

    # await metrics_collector.start_collection(
    #     session=session, agent_name=ctx.job.agent_name, session_id=session_id,
    #     account_id=account_id, user_id=user_id, orchestrator=orchestrator,
    # )

    # --- Run session until completion ---
    await start_session_and_greet(session, agent, ctx)
    # await handle_session_end(session, session_id, account_id, orchestrator, analytics_service)
    
    logger.info("✅ Agent session completed")


# -------------------------------------------------------------------
# Worker options & main
# -------------------------------------------------------------------
def create_worker_options() -> WorkerOptions:
    """Creates worker options from environment variables."""
    return WorkerOptions(
        entrypoint_fnc=entrypoint,
        ws_url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
        agent_name="boboyii-dispatcher",
        worker_type=WorkerType.PUBLISHER,
    )

def main():
    """Main function to run the agent worker."""
    logger.info("Starting Boboyii Dispatcher Agent...")
    cli.run_app(create_worker_options())


if __name__ == "__main__":
    main()