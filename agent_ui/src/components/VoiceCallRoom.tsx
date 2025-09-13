import React, { useState, useEffect } from 'react';
import { 
  useParticipants, 
  RoomAudioRenderer,
  useLocalParticipant,
  useConnectionState,
  useDataChannel,
  useRoomContext
} from '@livekit/components-react';
import { ConnectionState } from 'livekit-client';
import { motion, AnimatePresence } from 'framer-motion';
import ParticipantTile from './ParticipantTile';
import VoiceControls from './VoiceControls';
import TranslationPanel from './TranslationPanel';

interface VoiceCallRoomProps {
  userName: string;
  userLanguage: string;
  userAvatar: string;
  roomId: string;
}

const VoiceCallRoom: React.FC<VoiceCallRoomProps> = ({
  userName,
  userLanguage,
  userAvatar,
  roomId
}) => {
  const participants = useParticipants();
  const { localParticipant } = useLocalParticipant();
  const connectionState = useConnectionState();
  const room = useRoomContext();
  
  const [isTranslationPanelOpen, setIsTranslationPanelOpen] = useState(false);
  const [translationMessages, setTranslationMessages] = useState<any[]>([]);
  const [voiceAgentEnabled, setVoiceAgentEnabled] = useState(true);
  const [agentStatus, setAgentStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  
  // Data channel for real-time communication with backend agents
  const { send } = useDataChannel('translation', (message) => {
    console.log('Received translation data:', message);
    // Handle incoming translation messages from backend agents
    if (message.payload) {
      try {
        const translationData = JSON.parse(new TextDecoder().decode(message.payload));
        setTranslationMessages(prev => [...prev.slice(-9), {
          id: Date.now(),
          timestamp: Date.now(),
          from: message.from,
          originalText: translationData.original,
          translatedText: translationData.translated,
          sourceLanguage: translationData.sourceLanguage,
          targetLanguage: translationData.targetLanguage,
        }]);
      } catch (e) {
        console.warn('Failed to parse translation data:', e);
      }
    }
  });

  useEffect(() => {
    const updateMetadata = async () => {
      if (localParticipant && connectionState === ConnectionState.Connected) {
        try {
          // Set participant metadata with language and avatar info
          await localParticipant.setMetadata(JSON.stringify({
            language: userLanguage,
            avatar: userAvatar,
            name: userName
          }));
          console.log('Metadata updated successfully');
        } catch (error) {
          console.warn('Failed to update participant metadata:', error);
          // Don't throw - this is not critical for the app to function
        }
      }
    };

    // Only update metadata when connected
    if (connectionState === ConnectionState.Connected) {
      // Add a small delay to ensure connection is fully established
      const timer = setTimeout(updateMetadata, 500);
      return () => clearTimeout(timer);
    }
  }, [localParticipant, connectionState, userLanguage, userAvatar, userName]);

  // Function to send preferences to backend agents
  const sendPreferencesToAgents = async () => {
    if (!send) return;
    
    const preferences = {
      type: 'user_preferences',
      language: userLanguage,
      avatar: userAvatar,
      voiceAgentEnabled,
      timestamp: Date.now()
    };
    
    try {
      const encoder = new TextEncoder();
      send(encoder.encode(JSON.stringify(preferences)), { topic: 'translation' });
      console.log('Sent preferences to agents:', preferences);
    } catch (error) {
      console.warn('Failed to send preferences to agents:', error);
    }
  };

  // Send preferences when voice agent setting changes
  useEffect(() => {
    if (connectionState === ConnectionState.Connected) {
      sendPreferencesToAgents();
    }
  }, [voiceAgentEnabled, connectionState]);

  // Monitor agent connection status
  useEffect(() => {
    // Check if there's a translation agent participant in the room
    const hasTranslationAgent = participants.some(p => 
      p.identity.includes('translation-agent') || 
      p.name?.includes('translation-agent') ||
      p.identity.includes('agent')
    );

    if (hasTranslationAgent) {
      setAgentStatus('connected');
    } else if (connectionState === ConnectionState.Connected) {
      // If we're connected but no agent, it might be connecting
      setAgentStatus('connecting');
    } else {
      setAgentStatus('disconnected');
    }
  }, [participants, connectionState]);

  const remoteParticipants = participants.filter(p => !p.isLocal);
  const hasRemoteParticipants = remoteParticipants.length > 0;

  return (
    <div className="relative h-screen overflow-hidden dark">
      {/* Audio Renderer - handles all audio playback */}
      <RoomAudioRenderer />
      
      {/* Main Content Area */}
      <div className="flex h-full pt-20 pb-24">
        {/* Participants Area */}
        <div className="flex-1 flex items-center justify-center p-8">
          {!hasRemoteParticipants ? (
            // Waiting for participants
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center max-w-md"
            >
              <div className="relative mb-8">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                  className="w-32 h-32 rounded-full border-4 border-primary-200 border-t-primary-600 mx-auto"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-20 h-20 bg-primary-500/20 rounded-full flex items-center justify-center">
                    <svg className="w-10 h-10 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <h2 className="text-3xl font-bold text-white mb-4">
                Waiting for participants...
              </h2>
              <p className="text-dark-300 text-lg mb-6">
                Share this room ID with others to start your conversation
              </p>
              
              {/* Room ID Display */}
              <div className="bg-dark-800 rounded-lg p-4 mb-6">
                <p className="text-sm text-dark-400 mb-2">Room ID</p>
                <div className="flex items-center justify-between">
                  <code className="text-primary-400 font-mono text-lg">{roomId}</code>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => navigator.clipboard.writeText(roomId)}
                    className="ml-3 px-3 py-1 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded transition-colors"
                  >
                    Copy
                  </motion.button>
                </div>
              </div>

              {/* Your Settings */}
              <div className="bg-dark-800 rounded-lg p-4">
                <p className="text-sm text-dark-400 mb-3">Your Settings</p>
                <div className="space-y-2 text-left">
                  <div className="flex items-center justify-between">
                    <span className="text-dark-300">Name:</span>
                    <span className="text-white">{userName}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-dark-300">Language:</span>
                    <span className="text-white">{userLanguage.toUpperCase()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-dark-300">Avatar:</span>
                    <span className="text-white">{userAvatar}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-dark-300">Translation Agent:</span>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        agentStatus === 'connected' ? 'bg-green-500' :
                        agentStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                        'bg-red-500'
                      }`}></div>
                      <span className={`text-sm ${
                        agentStatus === 'connected' ? 'text-green-400' :
                        agentStatus === 'connecting' ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {agentStatus === 'connected' ? 'Active' :
                         agentStatus === 'connecting' ? 'Connecting...' :
                         'Disconnected'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ) : (
            // Active conversation view
            <div className="w-full max-w-6xl mx-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 h-full">
                {/* Local Participant */}
                <motion.div
                  initial={{ opacity: 0, x: -50 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <ParticipantTile
                    participant={localParticipant}
                    isLocal={true}
                    language={userLanguage}
                    avatar={userAvatar}
                    userName={userName}
                  />
                </motion.div>

                {/* Remote Participants */}
                <AnimatePresence>
                  {remoteParticipants.map((participant, index) => (
                    <motion.div
                      key={participant.sid}
                      initial={{ opacity: 0, x: 50 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 50 }}
                      transition={{ delay: 0.3 + index * 0.1 }}
                    >
                      <ParticipantTile
                        participant={participant}
                        isLocal={false}
                        language="auto" // Will be detected from metadata
                        avatar="default"
                        userName={participant.name || 'Remote User'}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          )}
        </div>

        {/* Translation Panel */}
        <AnimatePresence>
          {isTranslationPanelOpen && (
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="w-96 bg-dark-800 border-l border-dark-600"
            >
              <TranslationPanel
                messages={translationMessages}
                onClose={() => setIsTranslationPanelOpen(false)}
                voiceAgentEnabled={voiceAgentEnabled}
                onToggleVoiceAgent={setVoiceAgentEnabled}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Controls */}
      <div className="absolute bottom-0 left-0 right-0 p-6">
        <VoiceControls
          onToggleTranslation={() => setIsTranslationPanelOpen(!isTranslationPanelOpen)}
          translationPanelOpen={isTranslationPanelOpen}
          voiceAgentEnabled={voiceAgentEnabled}
          onToggleVoiceAgent={setVoiceAgentEnabled}
          participantCount={participants.length}
        />
      </div>
    </div>
  );
};

export default VoiceCallRoom;
