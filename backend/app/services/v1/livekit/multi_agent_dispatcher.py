"""
Multi-Agent Dispatcher for LiveKit Translation Rooms.
This service ensures that each user gets their own dedicated translation agent.
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from livekit import api, rtc
from livekit.agents import JobContext

from app.core.config import get_settings
from app.models.domain.profiles import UserLanguageProfile, SupportedLanguage
from app.services.livekit.room_manager import PatternBRoomManager


@dataclass
class AgentDispatchInfo:
    """Information about an agent dispatch."""
    user_identity: str
    agent_name: str
    metadata: dict
    dispatch_id: Optional[str] = None


class MultiAgentDispatcher:
    """
    Service for dispatching multiple translation agents to a room.
    Each user gets their own dedicated agent for optimal translation performance.
    """
    
    def __init__(self, room_manager: PatternBRoomManager):
        self.room_manager = room_manager
        self._livekit_api = None
        self.active_dispatches: Dict[str, List[AgentDispatchInfo]] = {}  # room_name -> [dispatches]
        
    def _get_livekit_api(self) -> api.LiveKitAPI:
        """Get or create LiveKit API client."""
        if self._livekit_api is None:
            settings = get_settings()
            self._livekit_api = api.LiveKitAPI(
                url=settings.livekit_url,
                api_key=settings.livekit_api_key,
                api_secret=settings.livekit_api_secret
            )
        return self._livekit_api
    
    async def dispatch_agents_for_room(self, room_name: str, user_identities: List[str]) -> Dict[str, str]:
        """
        Dispatch one agent per user to a room.
        
        Args:
            room_name: The room to dispatch agents to
            user_identities: List of user identities that need agents
            
        Returns:
            Dict mapping user_identity -> dispatch_id
        """
        try:
            lkapi = self._get_livekit_api()
            dispatch_results = {}
            
            # Create agent dispatches for each user
            for user_identity in user_identities:
                try:
                    # Get user profile
                    profile = await self.room_manager.get_user_profile(user_identity)
                    if not profile:
                        logging.warning(f"No profile found for user {user_identity}, skipping agent dispatch")
                        continue
                    
                    # Prepare agent metadata
                    agent_metadata = {
                        "user_identity": user_identity,
                        "native_language": profile.native_language.value,
                        "translation_preferences": profile.translation_preferences,
                        "room_type": "translation",
                        "use_realtime": True,
                        "language": profile.native_language.value
                    }
                    
                    # Create dispatch request
                    dispatch_request = api.CreateAgentDispatchRequest(
                        agent_name="translation-agent",
                        room=room_name,
                        metadata=json.dumps(agent_metadata)
                    )
                    
                    # Dispatch the agent
                    dispatch = await lkapi.agent_dispatch.create_dispatch(dispatch_request)
                    
                    # Store dispatch info
                    dispatch_info = AgentDispatchInfo(
                        user_identity=user_identity,
                        agent_name="translation-agent",
                        metadata=agent_metadata,
                        dispatch_id=dispatch.id
                    )
                    
                    if room_name not in self.active_dispatches:
                        self.active_dispatches[room_name] = []
                    self.active_dispatches[room_name].append(dispatch_info)
                    
                    dispatch_results[user_identity] = dispatch.id
                    
                    logging.info(f"✅ Dispatched agent for user {user_identity} to room {room_name} (dispatch_id: {dispatch.id})")
                    
                except Exception as e:
                    logging.error(f"❌ Failed to dispatch agent for user {user_identity}: {e}")
                    continue
            
            return dispatch_results
            
        except Exception as e:
            logging.error(f"❌ Error dispatching agents to room {room_name}: {e}")
            return {}
    
    async def dispatch_agent_for_user(self, room_name: str, user_identity: str) -> Optional[str]:
        """
        Dispatch a single agent for a specific user.
        
        Args:
            room_name: The room to dispatch agent to
            user_identity: The user that needs an agent
            
        Returns:
            Dispatch ID if successful, None otherwise
        """
        results = await self.dispatch_agents_for_room(room_name, [user_identity])
        return results.get(user_identity)
    
    async def list_room_dispatches(self, room_name: str) -> List[AgentDispatchInfo]:
        """List all agent dispatches for a room."""
        try:
            lkapi = self._get_livekit_api()
            dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
            
            dispatch_infos = []
            for dispatch in dispatches:
                try:
                    metadata = json.loads(dispatch.metadata or "{}")
                    dispatch_info = AgentDispatchInfo(
                        user_identity=metadata.get("user_identity", "unknown"),
                        agent_name=dispatch.agent_name,
                        metadata=metadata,
                        dispatch_id=dispatch.id
                    )
                    dispatch_infos.append(dispatch_info)
                except Exception as e:
                    logging.warning(f"Failed to parse dispatch metadata: {e}")
                    continue
            
            return dispatch_infos
            
        except Exception as e:
            logging.error(f"Failed to list dispatches for room {room_name}: {e}")
            return []
    
    async def cleanup_room_dispatches(self, room_name: str) -> bool:
        """Clean up all agent dispatches for a room."""
        try:
            if room_name in self.active_dispatches:
                del self.active_dispatches[room_name]
            
            # Note: LiveKit doesn't provide a direct way to cancel dispatches
            # They will be cleaned up automatically when the room is deleted
            # or when the agents disconnect
            
            logging.info(f"Cleaned up dispatch tracking for room {room_name}")
            return True
            
        except Exception as e:
            logging.error(f"Error cleaning up dispatches for room {room_name}: {e}")
            return False
    
    def get_room_agent_count(self, room_name: str) -> int:
        """Get the number of agents dispatched to a room."""
        return len(self.active_dispatches.get(room_name, []))
    
    def get_room_agent_users(self, room_name: str) -> List[str]:
        """Get the list of users that have agents in a room."""
        return [dispatch.user_identity for dispatch in self.active_dispatches.get(room_name, [])]
    
    async def ensure_agents_for_participants(self, room_name: str, participant_identities: List[str]) -> Dict[str, str]:
        """
        Ensure that all participants have dedicated agents.
        Only dispatches agents for participants that don't already have them.
        
        Args:
            room_name: The room name
            participant_identities: List of participant identities in the room
            
        Returns:
            Dict mapping user_identity -> dispatch_id for newly dispatched agents
        """
        try:
            # Get current dispatches for the room
            current_dispatches = await self.list_room_dispatches(room_name)
            current_users = {dispatch.user_identity for dispatch in current_dispatches}
            
            # Find participants that don't have agents yet
            users_needing_agents = [
                user_id for user_id in participant_identities 
                if user_id not in current_users
            ]
            
            if not users_needing_agents:
                logging.info(f"All participants in room {room_name} already have agents")
                return {}
            
            logging.info(f"Dispatching agents for {len(users_needing_agents)} participants in room {room_name}")
            
            # Dispatch agents for users that need them
            new_dispatches = await self.dispatch_agents_for_room(room_name, users_needing_agents)
            
            return new_dispatches
            
        except Exception as e:
            logging.error(f"Error ensuring agents for participants in room {room_name}: {e}")
            return {}
    
    def get_dispatcher_stats(self) -> Dict:
        """Get statistics about the dispatcher."""
        total_dispatches = sum(len(dispatches) for dispatches in self.active_dispatches.values())
        
        return {
            "active_rooms": len(self.active_dispatches),
            "total_dispatches": total_dispatches,
            "rooms": {
                room_name: {
                    "agent_count": len(dispatches),
                    "users": [d.user_identity for d in dispatches]
                }
                for room_name, dispatches in self.active_dispatches.items()
            }
        }


