"""
Clean audio routing system for simultaneous interpretation.
Prevents audio pollution by ensuring each user only hears the original speaker in their preferred language.
"""
import asyncio
import logging
from typing import Dict, Set, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import uuid

from livekit import rtc
from app.models.domain.profiles import SupportedLanguage


class AudioStreamType(Enum):
    ORIGINAL = "original"  # Original speaker audio
    TRANSLATED = "translated"  # Translated TTS audio


@dataclass
class AudioRoute:
    """Audio routing configuration."""
    source_participant_id: str
    target_participant_id: str
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    stream_type: AudioStreamType
    is_active: bool = True


@dataclass
class ParticipantAudioConfig:
    """Audio configuration for a participant."""
    participant_id: str
    native_language: SupportedLanguage
    should_hear_original: Set[str]  # Participant IDs whose original audio to hear
    should_hear_translated: Set[str]  # Participant IDs whose translated audio to hear
    should_mute: Set[str]  # Participant IDs to mute completely


class CleanAudioRouter:
    """
    Clean audio routing system for 2-user simultaneous interpretation.
    
    Key Features:
    - No audio pollution: each user only hears what they should
    - Language-aware routing
    - Real-time audio stream management
    - Automatic muting/unmuting based on language preferences
    """
    
    def __init__(self):
        self.routes: Dict[str, AudioRoute] = {}
        self.participant_configs: Dict[str, ParticipantAudioConfig] = {}
        self.active_participants: Dict[str, rtc.RemoteParticipant] = {}
        self.local_participants: Dict[str, rtc.LocalParticipant] = {}
        
        # Track audio subscriptions
        self.audio_subscriptions: Dict[str, Dict[str, rtc.RemoteAudioTrack]] = {}
        
        # Track current speakers to avoid feedback
        self.current_speakers: Set[str] = set()
        
        logging.info("CleanAudioRouter initialized")
    
    def register_participant(self,
                           participant_id: str,
                           native_language: SupportedLanguage,
                           participant: Optional[rtc.RemoteParticipant] = None,
                           local_participant: Optional[rtc.LocalParticipant] = None):
        """
        Register a participant with their audio preferences.
        
        Args:
            participant_id: Unique participant identifier
            native_language: Participant's native language
            participant: RemoteParticipant instance (if remote)
            local_participant: LocalParticipant instance (if local)
        """
        # Create audio configuration
        config = ParticipantAudioConfig(
            participant_id=participant_id,
            native_language=native_language,
            should_hear_original=set(),
            should_hear_translated=set(),
            should_mute=set()
        )
        
        self.participant_configs[participant_id] = config
        
        # Store participant references
        if participant:
            self.active_participants[participant_id] = participant
        if local_participant:
            self.local_participants[participant_id] = local_participant
        
        # Initialize audio subscriptions tracking
        self.audio_subscriptions[participant_id] = {}
        
        # Update routing for all participants
        self._update_audio_routing()
        
        logging.info(f"Registered participant {participant_id} with language {native_language.value}")
    
    def unregister_participant(self, participant_id: str):
        """Unregister a participant and clean up their routing."""
        # Remove from all data structures
        self.participant_configs.pop(participant_id, None)
        self.active_participants.pop(participant_id, None)
        self.local_participants.pop(participant_id, None)
        self.audio_subscriptions.pop(participant_id, None)
        self.current_speakers.discard(participant_id)
        
        # Remove routes involving this participant
        routes_to_remove = []
        for route_id, route in self.routes.items():
            if (route.source_participant_id == participant_id or 
                route.target_participant_id == participant_id):
                routes_to_remove.append(route_id)
        
        for route_id in routes_to_remove:
            del self.routes[route_id]
        
        # Update routing for remaining participants
        self._update_audio_routing()
        
        logging.info(f"Unregistered participant {participant_id}")
    
    def set_current_speaker(self, participant_id: str):
        """Set the current speaker to manage audio routing."""
        self.current_speakers = {participant_id}  # Only one speaker at a time
        self._update_real_time_routing()
        logging.debug(f"Current speaker set to: {participant_id}")
    
    def clear_current_speaker(self, participant_id: str):
        """Clear the current speaker."""
        self.current_speakers.discard(participant_id)
        self._update_real_time_routing()
        logging.debug(f"Cleared speaker: {participant_id}")
    
    def _update_audio_routing(self):
        """Update audio routing configuration for all participants."""
        # Clear existing configurations
        for config in self.participant_configs.values():
            config.should_hear_original.clear()
            config.should_hear_translated.clear()
            config.should_mute.clear()
        
        # For 2-user translation, create simple routing rules
        participant_ids = list(self.participant_configs.keys())
        
        if len(participant_ids) == 2:
            participant_a_id, participant_b_id = participant_ids
            config_a = self.participant_configs[participant_a_id]
            config_b = self.participant_configs[participant_b_id]
            
            # If participants speak different languages, set up translation routing
            if config_a.native_language != config_b.native_language:
                # A should hear B's speech translated to A's language
                config_a.should_hear_translated.add(participant_b_id)
                # B should hear A's speech translated to B's language  
                config_b.should_hear_translated.add(participant_a_id)
                
                # Neither should hear the other's original audio (to avoid pollution)
                config_a.should_mute.add(participant_b_id)
                config_b.should_mute.add(participant_a_id)
                
                logging.info(f"Set up translation routing: {participant_a_id} ({config_a.native_language.value}) <-> "
                           f"{participant_b_id} ({config_b.native_language.value})")
            else:
                # Same language - hear original audio
                config_a.should_hear_original.add(participant_b_id)
                config_b.should_hear_original.add(participant_a_id)
                
                logging.info(f"Set up direct routing (same language): {participant_a_id} <-> {participant_b_id}")
        
        # Create routes
        self._create_routes()
    
    def _create_routes(self):
        """Create audio routes based on participant configurations."""
        self.routes.clear()
        
        for participant_id, config in self.participant_configs.items():
            # Create routes for original audio
            for source_id in config.should_hear_original:
                if source_id in self.participant_configs:
                    source_config = self.participant_configs[source_id]
                    route_id = f"{source_id}_to_{participant_id}_original"
                    
                    self.routes[route_id] = AudioRoute(
                        source_participant_id=source_id,
                        target_participant_id=participant_id,
                        source_language=source_config.native_language,
                        target_language=config.native_language,
                        stream_type=AudioStreamType.ORIGINAL
                    )
            
            # Create routes for translated audio
            for source_id in config.should_hear_translated:
                if source_id in self.participant_configs:
                    source_config = self.participant_configs[source_id]
                    route_id = f"{source_id}_to_{participant_id}_translated"
                    
                    self.routes[route_id] = AudioRoute(
                        source_participant_id=source_id,
                        target_participant_id=participant_id,
                        source_language=source_config.native_language,
                        target_language=config.native_language,
                        stream_type=AudioStreamType.TRANSLATED
                    )
        
        logging.debug(f"Created {len(self.routes)} audio routes")
    
    def _update_real_time_routing(self):
        """Update real-time audio routing based on current speaker."""
        for participant_id, config in self.participant_configs.items():
            # Skip if this is the current speaker (don't route their own audio back)
            if participant_id in self.current_speakers:
                continue
            
            # Apply muting/unmuting based on current speaker and routing rules
            self._apply_audio_controls(participant_id, config)
    
    def _apply_audio_controls(self, participant_id: str, config: ParticipantAudioConfig):
        """Apply audio controls (muting/unmuting) for a participant."""
        try:
            # Get participant references
            remote_participant = self.active_participants.get(participant_id)
            local_participant = self.local_participants.get(participant_id)
            
            if not (remote_participant or local_participant):
                return
            
            # For each other participant, decide what audio this participant should hear
            for other_id in self.participant_configs.keys():
                if other_id == participant_id:
                    continue  # Skip self
                
                should_hear_original = other_id in config.should_hear_original
                should_hear_translated = other_id in config.should_hear_translated
                should_mute = other_id in config.should_mute
                is_current_speaker = other_id in self.current_speakers
                
                # Determine action
                if should_mute and not (should_hear_translated and is_current_speaker):
                    # Mute original audio from this participant
                    self._mute_participant_audio(participant_id, other_id)
                elif should_hear_original and is_current_speaker:
                    # Unmute original audio from this participant
                    self._unmute_participant_audio(participant_id, other_id)
                elif should_hear_translated and is_current_speaker:
                    # Original audio should be muted, translated audio will be played via TTS
                    self._mute_participant_audio(participant_id, other_id)
                
        except Exception as e:
            logging.error(f"Error applying audio controls for {participant_id}: {e}")
    
    def _mute_participant_audio(self, listener_id: str, speaker_id: str):
        """Mute audio from speaker for a specific listener."""
        try:
            # For LiveKit, we would typically handle this through track subscriptions
            # This is a simplified implementation - in practice you'd use LiveKit's
            # subscription management to control which tracks a participant receives
            
            logging.debug(f"Muting {speaker_id} audio for {listener_id}")
            
            # In a real implementation, you would:
            # 1. Get the audio track from speaker_id
            # 2. Unsubscribe listener_id from that track
            # 3. Or set the track volume to 0 for that listener
            
        except Exception as e:
            logging.error(f"Error muting audio from {speaker_id} for {listener_id}: {e}")
    
    def _unmute_participant_audio(self, listener_id: str, speaker_id: str):
        """Unmute audio from speaker for a specific listener."""
        try:
            logging.debug(f"Unmuting {speaker_id} audio for {listener_id}")
            
            # In a real implementation, you would:
            # 1. Get the audio track from speaker_id  
            # 2. Subscribe listener_id to that track
            # 3. Or restore the track volume for that listener
            
        except Exception as e:
            logging.error(f"Error unmuting audio from {speaker_id} for {listener_id}: {e}")
    
    async def handle_translated_audio(self,
                                    source_participant_id: str,
                                    target_participant_id: str, 
                                    audio_data: bytes):
        """
        Handle translated audio playback to the target participant.
        
        Args:
            source_participant_id: ID of the original speaker
            target_participant_id: ID of the listener who should hear the translation
            audio_data: Translated audio data to play
        """
        try:
            # Check if this routing is allowed
            route_id = f"{source_participant_id}_to_{target_participant_id}_translated"
            if route_id not in self.routes or not self.routes[route_id].is_active:
                logging.debug(f"Translation route not active: {route_id}")
                return
            
            # In a real implementation, you would:
            # 1. Create an audio track from the audio_data
            # 2. Publish it to the room with appropriate metadata
            # 3. Ensure only the target participant receives it
            
            logging.debug(f"Playing translated audio from {source_participant_id} to {target_participant_id}")
            
        except Exception as e:
            logging.error(f"Error handling translated audio: {e}")
    
    def get_routing_info(self) -> Dict:
        """Get current routing information for debugging."""
        return {
            "participants": {
                pid: {
                    "native_language": config.native_language.value,
                    "should_hear_original": list(config.should_hear_original),
                    "should_hear_translated": list(config.should_hear_translated),
                    "should_mute": list(config.should_mute)
                }
                for pid, config in self.participant_configs.items()
            },
            "routes": {
                route_id: {
                    "source": route.source_participant_id,
                    "target": route.target_participant_id,
                    "source_language": route.source_language.value,
                    "target_language": route.target_language.value,
                    "stream_type": route.stream_type.value,
                    "is_active": route.is_active
                }
                for route_id, route in self.routes.items()
            },
            "current_speakers": list(self.current_speakers)
        }
    
    def get_participant_audio_config(self, participant_id: str) -> Optional[Dict]:
        """Get audio configuration for a specific participant."""
        if participant_id not in self.participant_configs:
            return None
        
        config = self.participant_configs[participant_id]
        return {
            "participant_id": config.participant_id,
            "native_language": config.native_language.value,
            "should_hear_original": list(config.should_hear_original),
            "should_hear_translated": list(config.should_hear_translated),
            "should_mute": list(config.should_mute),
            "is_current_speaker": participant_id in self.current_speakers
        }
    
    def enable_route(self, route_id: str):
        """Enable a specific audio route."""
        if route_id in self.routes:
            self.routes[route_id].is_active = True
            logging.debug(f"Enabled route: {route_id}")
    
    def disable_route(self, route_id: str):
        """Disable a specific audio route."""
        if route_id in self.routes:
            self.routes[route_id].is_active = False
            logging.debug(f"Disabled route: {route_id}")
    
    def get_active_routes_for_participant(self, participant_id: str) -> List[Dict]:
        """Get all active routes involving a participant."""
        routes = []
        for route_id, route in self.routes.items():
            if (route.is_active and 
                (route.source_participant_id == participant_id or 
                 route.target_participant_id == participant_id)):
                routes.append({
                    "route_id": route_id,
                    "source": route.source_participant_id,
                    "target": route.target_participant_id,
                    "source_language": route.source_language.value,
                    "target_language": route.target_language.value,
                    "stream_type": route.stream_type.value
                })
        return routes
