import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TranslationMessage {
  participantId: string;
  participantName?: string;
  originalText: string;
  translatedText: string;
  fromLanguage: string;
  toLanguage: string;
  timestamp: number;
}

interface TranslationPanelProps {
  messages: TranslationMessage[];
  onClose: () => void;
  voiceAgentEnabled: boolean;
  onToggleVoiceAgent: (enabled: boolean) => void;
}

const TranslationPanel: React.FC<TranslationPanelProps> = ({
  messages,
  onClose,
  voiceAgentEnabled,
  onToggleVoiceAgent
}) => {
  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getLanguageFlag = (languageCode: string) => {
    const flags: Record<string, string> = {
      'en': '🇺🇸',
      'es': '🇪🇸',
      'fr': '🇫🇷',
      'de': '🇩🇪',
      'it': '🇮🇹',
      'pt': '🇵🇹',
      'ru': '🇷🇺',
      'ja': '🇯🇵',
      'ko': '🇰🇷',
      'zh': '🇨🇳',
      'ar': '🇸🇦',
      'hi': '🇮🇳',
    };
    return flags[languageCode] || '🌐';
  };

  return (
    <div className="h-full flex flex-col dark">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dark-600">
        <h2 className="text-lg font-semibold text-white flex items-center">
          <svg className="w-5 h-5 mr-2 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
          </svg>
          Live Translation
        </h2>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onClose}
          className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
        >
          <svg className="w-5 h-5 text-dark-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </motion.button>
      </div>

      {/* Voice Agent Toggle */}
      <div className="p-4 border-b border-dark-600">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-white font-medium mb-1">Voice Agent</h3>
            <p className="text-dark-300 text-sm">
              {voiceAgentEnabled ? 'Actively dubbing conversations' : 'Translation text only'}
            </p>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onToggleVoiceAgent(!voiceAgentEnabled)}
            className={`relative w-12 h-6 rounded-full transition-colors duration-200 ${
              voiceAgentEnabled ? 'bg-green-500' : 'bg-dark-600'
            }`}
          >
            <motion.div
              animate={{ x: voiceAgentEnabled ? 24 : 2 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              className="absolute top-1 w-4 h-4 bg-white rounded-full"
            />
          </motion.button>
        </div>
        
        {voiceAgentEnabled && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-3 p-3 bg-green-500/10 border border-green-500/20 rounded-lg"
          >
            <div className="flex items-center space-x-2">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-2 h-2 bg-green-400 rounded-full"
              />
              <span className="text-green-400 text-sm font-medium">
                AI Voice Agent Active
              </span>
            </div>
            <p className="text-green-300 text-xs mt-1">
              Real-time voice dubbing enabled
            </p>
          </motion.div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <svg className="w-12 h-12 text-dark-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-dark-400 text-sm">
              Translation messages will appear here
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={`${message.participantId}-${message.timestamp}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: index * 0.1 }}
                className="bg-dark-700/50 rounded-lg p-3 border border-dark-600/50 dark:bg-dark-700/50 dark:border-dark-600/50"
              >
                {/* Message Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 bg-primary-500/20 rounded-full flex items-center justify-center">
                      <span className="text-primary-400 text-xs font-medium">
                        {message.participantName?.charAt(0) || 'U'}
                      </span>
                    </div>
                    <span className="text-white text-sm font-medium">
                      {message.participantName || 'User'}
                    </span>
                  </div>
                  <span className="text-dark-400 text-xs">
                    {formatTime(message.timestamp)}
                  </span>
                </div>

                {/* Original Text */}
                <div className="mb-3">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-lg">{getLanguageFlag(message.fromLanguage)}</span>
                    <span className="text-dark-300 text-xs uppercase">
                      {message.fromLanguage}
                    </span>
                  </div>
                  <p className="text-dark-200 text-sm bg-dark-800/50 rounded p-2">
                    {message.originalText}
                  </p>
                </div>

                {/* Translation Arrow */}
                <div className="flex justify-center mb-3">
                  <svg className="w-4 h-4 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>

                {/* Translated Text */}
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-lg">{getLanguageFlag(message.toLanguage)}</span>
                    <span className="text-dark-300 text-xs uppercase">
                      {message.toLanguage}
                    </span>
                    {voiceAgentEnabled && (
                      <div className="flex items-center space-x-1 ml-auto">
                        <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.816L4.846 14H2a1 1 0 01-1-1V7a1 1 0 011-1h2.846l3.537-2.816a1 1 0 011.617.816zM16.446 4.88c.176-.177.46-.177.636 0l.708.708a.5.5 0 010 .707L15.5 8.586l2.29 2.29a.5.5 0 010 .708l-.708.708c-.176.176-.46.176-.636 0L14.086 9.93l-2.29 2.29c-.176.177-.46.177-.636 0l-.708-.708a.5.5 0 010-.707L12.742 8.5l-2.29-2.29a.5.5 0 010-.708l.708-.708c.176-.176.46-.176.636 0l2.29 2.29 2.36-2.36z" clipRule="evenodd" />
                        </svg>
                        <span className="text-green-400 text-xs">Voiced</span>
                      </div>
                    )}
                  </div>
                  <p className="text-white text-sm bg-primary-500/10 border border-primary-500/20 rounded p-2">
                    {message.translatedText}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-dark-600">
        <div className="text-center">
          <p className="text-dark-400 text-xs">
            Powered by AI Translation Engine
          </p>
        </div>
      </div>
    </div>
  );
};

export default TranslationPanel;
