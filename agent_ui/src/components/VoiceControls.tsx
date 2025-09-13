import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useTrackToggle, useDisconnectButton, useLocalParticipant } from '@livekit/components-react';
import { Track } from 'livekit-client';

interface VoiceControlsProps {
  onToggleTranslation: () => void;
  translationPanelOpen: boolean;
  voiceAgentEnabled: boolean;
  onToggleVoiceAgent: (enabled: boolean) => void;
  participantCount: number;
}

const VoiceControls: React.FC<VoiceControlsProps> = ({
  onToggleTranslation,
  translationPanelOpen,
  voiceAgentEnabled,
  onToggleVoiceAgent,
  participantCount
}) => {
  const { toggle: toggleMic, enabled: micEnabled } = useTrackToggle({
    source: Track.Source.Microphone
  });
  const { localParticipant } = useLocalParticipant();
  const { buttonProps: disconnectProps } = useDisconnectButton({});
  const [showSettings, setShowSettings] = useState(false);
  
  // Audio settings
  const handleAudioSettings = async () => {
    if (!localParticipant) return;
    
    try {
      // Get available audio devices
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices.filter(device => device.kind === 'audioinput');
      console.log('Available audio inputs:', audioInputs);
      
      // This could trigger a device selection modal
      setShowSettings(!showSettings);
    } catch (error) {
      console.warn('Could not get audio devices:', error);
    }
  };

  const controlButtons = [
    {
      id: 'microphone',
      icon: micEnabled ? (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
      ) : (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-3a1 1 0 011-1h1m0 0V9a2 2 0 012-2h2m0 0V6a2 2 0 012-2h2a2 2 0 012 2v1m0 0v1a2 2 0 002 2h1m0 0v3a1 1 0 01-1 1h-1.586l-4.707 4.707A1 1 0 019 20v-6.586a1 1 0 01.293-.707l4.414-4.414A1 1 0 0115 8h.586a1 1 0 01.707.293L20 12" />
        </svg>
      ),
      label: micEnabled ? 'Mute' : 'Unmute',
      onClick: () => toggleMic(),
      active: micEnabled,
      variant: micEnabled ? 'primary' : 'danger'
    },
    {
      id: 'audio-settings',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      label: 'Audio Settings',
      onClick: handleAudioSettings,
      active: showSettings,
      variant: 'secondary' as const
    },
    {
      id: 'voice-agent',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
      label: voiceAgentEnabled ? 'Agent ON' : 'Agent OFF',
      onClick: () => onToggleVoiceAgent(!voiceAgentEnabled),
      active: voiceAgentEnabled,
      variant: voiceAgentEnabled ? 'success' : 'secondary'
    },
    {
      id: 'translation',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
      ),
      label: translationPanelOpen ? 'Hide Chat' : 'Show Chat',
      onClick: onToggleTranslation,
      active: translationPanelOpen,
      variant: 'secondary'
    }
  ];

  const getButtonStyles = (variant: string, active: boolean) => {
    const baseStyles = "w-14 h-14 rounded-full flex items-center justify-center transition-all duration-200 border-2";
    
    switch (variant) {
      case 'primary':
        return `${baseStyles} ${active 
          ? 'bg-primary-600 border-primary-500 text-white hover:bg-primary-700' 
          : 'bg-dark-600 border-dark-500 text-dark-300 hover:bg-dark-500'
        }`;
      case 'danger':
        return `${baseStyles} bg-red-600 border-red-500 text-white hover:bg-red-700`;
      case 'success':
        return `${baseStyles} ${active
          ? 'bg-green-600 border-green-500 text-white hover:bg-green-700'
          : 'bg-dark-600 border-dark-500 text-dark-300 hover:bg-dark-500'
        }`;
      case 'secondary':
      default:
        return `${baseStyles} ${active
          ? 'bg-primary-600/20 border-primary-500 text-primary-400 hover:bg-primary-600/30'
          : 'bg-dark-600 border-dark-500 text-dark-300 hover:bg-dark-500'
        }`;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center justify-center dark"
    >
      <div className="glass-effect rounded-2xl p-4 border border-dark-600/50 dark:border-dark-600/50">
        <div className="flex items-center space-x-4">
          {/* Participant Count */}
          <div className="flex items-center space-x-2 px-4 py-2 bg-dark-700/50 rounded-lg">
            <svg className="w-5 h-5 text-primary-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
            </svg>
            <span className="text-white font-medium">{participantCount}</span>
          </div>

          {/* Control Buttons */}
          <div className="flex items-center space-x-3">
            {controlButtons.map((button) => (
              <motion.button
                key={button.id}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={button.onClick}
                className={getButtonStyles(button.variant, button.active)}
                title={button.label}
              >
                {button.icon}
              </motion.button>
            ))}
          </div>

          {/* Voice Agent Status */}
          {voiceAgentEnabled && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center space-x-2 px-3 py-2 bg-green-600/20 border border-green-500/30 rounded-lg"
            >
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-2 h-2 bg-green-400 rounded-full"
              />
              <span className="text-green-400 text-sm font-medium">Agent Active</span>
            </motion.div>
          )}

          {/* Disconnect Button */}
          <div className="ml-4 pl-4 border-l border-dark-600">
            <button
              onClick={disconnectProps.onClick}
              className="w-12 h-12 bg-red-600 hover:bg-red-700 rounded-full flex items-center justify-center text-white transition-colors hover:scale-105 active:scale-95"
              title="Leave Room"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default VoiceControls;
