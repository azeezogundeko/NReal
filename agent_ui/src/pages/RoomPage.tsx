import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { Room } from 'livekit-client';
import { RoomContext } from '@livekit/components-react';
import '@livekit/components-styles';
import VoiceCallRoom from '../components/VoiceCallRoom';
import ConnectionStatus from '../components/ConnectionStatus';
import { motion } from 'framer-motion';
import { apiService } from '../services/api';

const RoomPage: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [room] = useState(() => new Room({
    // Audio-focused configuration for voice translation
    adaptiveStream: true,
    dynacast: true,
    audioCaptureDefaults: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      sampleRate: 48000,
      channelCount: 1,
    },
    // Minimal video config since this is primarily audio-based
    videoCaptureDefaults: {
      resolution: {
        width: 640,
        height: 480,
        frameRate: 15,
      },
    },
    // Enable audio by default for voice calls
    publishDefaults: {
      simulcast: false, // Not needed for audio-focused app
    },
  }));
  
  const [isConnecting, setIsConnecting] = useState(true);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  
  // Get user configuration from URL params
  const userName = searchParams.get('userName') || 'Anonymous';
  const userLanguage = searchParams.get('language') || 'en';
  const userAvatar = searchParams.get('avatar') || 'default';


  useEffect(() => {
    if (!roomId) {
      navigate('/');
      return;
    }

    const connectToRoom = async () => {
      try {
        setIsConnecting(true);
        setConnectionError(null);

        // First, ensure user profile exists
        await apiService.getOrCreateUserProfile(userName, userLanguage, userAvatar);
        
        // Create or ensure room exists in backend
        try {
          await apiService.createRoom({
            host_identity: userName,
            room_name: roomId,
            max_participants: 50
          });
          console.log('Room created or already exists:', roomId);
        } catch (roomError: any) {
          // Room might already exist, that's okay
          console.log('Room creation info:', roomError?.message || 'Room may already exist');
        }
        
        // Generate token and get server URL from backend
        const tokenResponse = await apiService.generateToken({
          user_identity: userName,
          room_name: roomId,
          user_metadata: {
            name: userName,
            language: userLanguage,
            avatar: userAvatar,
          }
        });
        
        const serverUrl = tokenResponse.ws_url;
        const token = tokenResponse.token;

        await room.connect(serverUrl, token);
        console.log('Connected to room:', roomId);
        
        // Note: Translation agent is automatically dispatched via token generation
        // No need to manually dispatch here as it's handled by RoomAgentDispatch in the token
        console.log('Translation agent will be automatically dispatched via token configuration');
        
        // Enable microphone by default for voice calls
        try {
          await room.localParticipant.setMicrophoneEnabled(true);
          console.log('Microphone enabled');
        } catch (micError) {
          console.warn('Could not enable microphone:', micError);
          // Don't fail the connection if mic access is denied
        }
        
        // Set up room event listeners for better data flow
        room.on('participantConnected', (participant) => {
          console.log('Participant connected:', participant.identity);
          
          // Note: Each participant gets their own agent automatically when they join
          // via their token generation process. No need to manually dispatch agents here.
          console.log(`Participant ${participant.identity} should have their own agent from token dispatch`);
        });
        
        room.on('participantDisconnected', (participant) => {
          console.log('Participant disconnected:', participant.identity);
        });
        
        room.on('dataReceived', (payload, participant) => {
          // Handle data from backend agents (translations, etc.)
          try {
            const data = JSON.parse(new TextDecoder().decode(payload));
            console.log('Received data from', participant?.identity, ':', data);
            // This can be used for real-time translations from backend agents
          } catch (e) {
            console.log('Received non-JSON data:', payload);
          }
        });
        
        setIsConnecting(false);
      } catch (error) {
        console.error('Failed to connect to room:', error);
        setConnectionError('Failed to connect to room. Please try again.');
        setIsConnecting(false);
      }
    };

    connectToRoom();

    return () => {
      room.disconnect();
    };
  }, [roomId, userName, userLanguage, userAvatar, navigate]);


  const handleLeaveRoom = () => {
    room.disconnect();
    navigate('/');
  };

  if (isConnecting) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black-950 via-black-900 to-black-950 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md w-full"
        >
          <div className="relative mb-8">
            <div className="w-24 h-24 sm:w-28 sm:h-28 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-6"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-12 h-12 sm:w-14 sm:h-14 bg-primary-500/20 rounded-full flex items-center justify-center backdrop-blur-sm">
                <svg className="w-6 h-6 sm:w-8 sm:h-8 text-primary-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
                </svg>
              </div>
            </div>
          </div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">Connecting to Room</h2>
            <p className="text-dark-300 text-base sm:text-lg mb-4">Setting up voice translation...</p>
            
            <div className="glass-effect rounded-lg p-4 border border-primary-500/20">
              <p className="text-sm text-dark-400 mb-1">Room ID</p>
              <p className="text-primary-400 font-mono text-sm sm:text-base break-all">{roomId}</p>
            </div>
          </motion.div>
          
          {/* Connection dots animation */}
          <motion.div 
            className="flex justify-center space-x-2 mt-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-2 h-2 bg-primary-500 rounded-full"
                animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
              />
            ))}
          </motion.div>
        </motion.div>
      </div>
    );
  }

  if (connectionError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black-950 via-black-900 to-black-950 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-lg w-full mx-auto"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
            className="w-20 h-20 sm:w-24 sm:h-24 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6 border border-red-500/30"
          >
            <svg className="w-10 h-10 sm:w-12 sm:h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">Connection Failed</h2>
            <p className="text-dark-300 text-base sm:text-lg mb-2">Unable to connect to the room</p>
            
            <div className="glass-effect rounded-lg p-4 mb-6 border border-red-500/20 bg-red-500/5">
              <p className="text-red-300 text-sm">{connectionError}</p>
            </div>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="space-y-3"
          >
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => window.location.reload()}
              className="w-full py-3 sm:py-4 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-all duration-200 flex items-center justify-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Try Again</span>
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleLeaveRoom}
              className="w-full py-3 sm:py-4 bg-dark-600 hover:bg-dark-500 text-white font-medium rounded-lg transition-all duration-200 flex items-center justify-center space-x-2 border border-dark-500"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m0 0V11a1 1 0 011-1h2a1 1 0 011 1v10m0 0h3a1 1 0 001-1V10m-11 0h11" />
              </svg>
              <span>Back to Home</span>
            </motion.button>
          </motion.div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black-950 via-black-900 to-black-950 dark" data-lk-theme="default">
      <RoomContext.Provider value={room}>
        {/* Responsive Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute top-0 left-0 right-0 z-20 p-3 sm:p-4 lg:p-6"
        >
          <div className="glass-effect rounded-xl border border-white/10 backdrop-blur-md">
            <div className="flex items-center justify-between p-3 sm:p-4">
              {/* Left section */}
              <div className="flex items-center space-x-2 sm:space-x-4 min-w-0 flex-1">
                <motion.h1 
                  className="text-lg sm:text-xl lg:text-2xl font-bold text-white truncate"
                  whileHover={{ scale: 1.02 }}
                >
                  Speech.app
                </motion.h1>
                <div className="hidden sm:block w-px h-6 bg-dark-600"></div>
                <div className="text-xs sm:text-sm text-dark-300 truncate">
                  <span className="hidden sm:inline">Room: </span>
                  <span className="text-primary-400 font-mono">{roomId}</span>
                </div>
              </div>
              
              {/* Right section */}
              <div className="flex items-center space-x-2 sm:space-x-3 lg:space-x-4">
                <ConnectionStatus />
                
                {/* Leave button - responsive */}
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleLeaveRoom}
                  className="px-3 py-2 sm:px-4 sm:py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-all duration-200 flex items-center space-x-1 sm:space-x-2 text-sm sm:text-base"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                  </svg>
                  <span className="hidden sm:inline">Leave</span>
                </motion.button>
              </div>
            </div>
            
            {/* Mobile room info */}
            <div className="sm:hidden px-3 pb-3">
              <div className="text-xs text-dark-400">
                Room ID: <span className="text-primary-400 font-mono break-all">{roomId}</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Main Room Interface */}
        <div className="pt-20 sm:pt-24 lg:pt-28">
          <VoiceCallRoom
            userName={userName}
            userLanguage={userLanguage}
            userAvatar={userAvatar}
            roomId={roomId || ''}
          />
        </div>
      </RoomContext.Provider>
    </div>
  );
};

export default RoomPage;
