import React, { useState, useEffect } from 'react';
import { Participant, Track } from 'livekit-client';
import { useTrackToggle, useIsSpeaking } from '@livekit/components-react';
import { motion } from 'framer-motion';

interface ParticipantTileProps {
  participant: Participant | null;
  isLocal: boolean;
  language: string;
  avatar: string;
  userName: string;
}

const AVATAR_EMOJIS: Record<string, string> = {
  default: '👤',
  professional: '👔',
  friendly: '😊',
  confident: '💪',
  gentle: '🌸',
  energetic: '⚡',
};

const ParticipantTile: React.FC<ParticipantTileProps> = ({
  participant,
  isLocal,
  language,
  avatar,
  userName
}) => {
  const isSpeaking = useIsSpeaking(participant || undefined);
  const { toggle: toggleMic, enabled: micEnabled } = useTrackToggle({
    source: Track.Source.Microphone
  });

  const [isTranslating, setIsTranslating] = useState(false);
  const [currentTranslation, setCurrentTranslation] = useState<string>('');
  const [participantMetadata, setParticipantMetadata] = useState<any>(null);

  useEffect(() => {
    if (participant?.metadata) {
      try {
        const metadata = JSON.parse(participant.metadata);
        setParticipantMetadata(metadata);
      } catch (e) {
        console.log('Could not parse participant metadata');
      }
    }
  }, [participant?.metadata]);

  // Mock translation simulation
  useEffect(() => {
    if (isSpeaking && !isLocal) {
      setIsTranslating(true);
      // Simulate translation delay
      const translationTimer = setTimeout(() => {
        setCurrentTranslation('Hello, how are you today?'); // Mock translation
        setIsTranslating(false);
      }, 1500);

      return () => clearTimeout(translationTimer);
    } else if (!isSpeaking) {
      setCurrentTranslation('');
      setIsTranslating(false);
    }
  }, [isSpeaking, isLocal]);

  const displayName = participantMetadata?.name || userName || participant?.name || 'Unknown';
  const participantLanguage = participantMetadata?.language || language;
  const participantAvatar = participantMetadata?.avatar || avatar;

  return (
    <motion.div
      animate={{
        scale: isSpeaking ? 1.02 : 1,
        boxShadow: isSpeaking 
          ? '0 0 30px rgba(255, 255, 255, 0.4)' 
          : '0 0 0px rgba(255, 255, 255, 0)'
      }}
      transition={{ duration: 0.3 }}
      className={`relative h-full min-h-[400px] bg-gradient-to-br from-black-900 to-black-800 rounded-2xl border-2 overflow-hidden dark:from-black-900 dark:to-black-800 ${
        isSpeaking 
          ? 'border-white shadow-lg shadow-white/25 dark:border-white dark:shadow-white/25' 
          : 'border-black-700 dark:border-black-700'
      }`}
    >
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="w-full h-full bg-gradient-to-br from-primary-400 to-primary-600"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 h-full flex flex-col items-center justify-center p-8">
        {/* Avatar */}
        <motion.div
          animate={{
            scale: isSpeaking ? 1.1 : 1,
            rotateY: isSpeaking ? [0, 5, -5, 0] : 0
          }}
          transition={{ 
            scale: { duration: 0.3 },
            rotateY: { duration: 2, repeat: isSpeaking ? Infinity : 0 }
          }}
          className={`relative w-32 h-32 mb-6 rounded-full flex items-center justify-center text-6xl ${
            isSpeaking ? 'bg-primary-500/20 shadow-lg shadow-primary-500/30' : 'bg-dark-600'
          }`}
        >
          {AVATAR_EMOJIS[participantAvatar] || '👤'}
          
          {/* Speaking Indicator */}
          {isSpeaking && (
            <motion.div
              animate={{ scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="absolute inset-0 rounded-full border-4 border-primary-400"
            />
          )}
        </motion.div>

        {/* Participant Info */}
        <div className="text-center mb-6">
          <h3 className="text-2xl font-bold text-white mb-2">
            {displayName}
            {isLocal && <span className="text-primary-400 ml-2">(You)</span>}
          </h3>
          <div className="flex items-center justify-center space-x-3 text-dark-300">
            <div className="flex items-center space-x-1">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.188-.196-.373-.396-.554-.6a19.098 19.098 0 01-3.107 3.567 1 1 0 01-1.334-1.49 17.087 17.087 0 003.13-3.733 18.992 18.992 0 01-1.487-2.494 1 1 0 111.79-.89c.234.47.489.928.764 1.372.417-.934.752-1.913.997-2.927H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.895L15.383 16h-4.764l-.724 1.447a1 1 0 11-1.788-.894l.99-1.98.019-.038 2.99-5.982A1 1 0 0113 8zm-1.382 6h2.764L13 11.236 11.618 14z" clipRule="evenodd" />
              </svg>
              <span className="uppercase text-sm">{participantLanguage}</span>
            </div>
            {participant && (
              <div className={`flex items-center space-x-1 ${
                participant.connectionQuality === 'excellent' ? 'text-green-400' :
                participant.connectionQuality === 'good' ? 'text-yellow-400' :
                'text-red-400'
              }`}>
                <div className="flex space-x-1">
                  <div className="w-1 h-3 bg-current rounded"></div>
                  <div className={`w-1 h-4 rounded ${
                    participant.connectionQuality === 'poor' ? 'bg-dark-500' : 'bg-current'
                  }`}></div>
                  <div className={`w-1 h-5 rounded ${
                    participant.connectionQuality === 'excellent' ? 'bg-current' : 'bg-dark-500'
                  }`}></div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Translation Display */}
        {(isTranslating || currentTranslation) && !isLocal && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="w-full max-w-sm bg-black-950/90 backdrop-blur-sm rounded-lg p-4 border border-white/30 dark:bg-black-950/90 dark:border-white/30"
          >
            {isTranslating ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="flex space-x-1">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.8, repeat: Infinity, delay: 0 }}
                    className="w-2 h-2 bg-primary-400 rounded-full"
                  />
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.8, repeat: Infinity, delay: 0.2 }}
                    className="w-2 h-2 bg-primary-400 rounded-full"
                  />
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.8, repeat: Infinity, delay: 0.4 }}
                    className="w-2 h-2 bg-primary-400 rounded-full"
                  />
                </div>
                <span className="text-primary-400 text-sm">Translating...</span>
              </div>
            ) : (
              <div>
                <div className="text-xs text-primary-400 mb-1">Translation</div>
                <div className="text-white text-sm">{currentTranslation}</div>
              </div>
            )}
          </motion.div>
        )}

        {/* Local Controls */}
        {isLocal && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-auto"
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => toggleMic()}
              className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-200 ${
                micEnabled
                  ? 'bg-black-700 hover:bg-black-600 text-white border-2 border-white'
                  : 'bg-red-600 hover:bg-red-700 text-white'
              }`}
            >
              {micEnabled ? (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-3a1 1 0 011-1h1m0 0V9a2 2 0 012-2h2m0 0V6a2 2 0 012-2h2a2 2 0 012 2v1m0 0v1a2 2 0 002 2h1m0 0v3a1 1 0 01-1 1h-1.586l-4.707 4.707A1 1 0 019 20v-6.586a1 1 0 01.293-.707l4.414-4.414A1 1 0 0115 8h.586a1 1 0 01.707.293L20 12" />
                </svg>
              )}
            </motion.button>
          </motion.div>
        )}

        {/* Voice Activity Indicator */}
        {isSpeaking && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute top-4 right-4"
          >
            <div className="flex items-center space-x-2 bg-primary-500/20 backdrop-blur-sm rounded-full px-3 py-1">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.5, repeat: Infinity }}
                className="w-2 h-2 bg-primary-400 rounded-full"
              />
              <span className="text-primary-400 text-xs font-medium">Speaking</span>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default ParticipantTile;
