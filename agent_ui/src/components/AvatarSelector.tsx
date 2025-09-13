import React from 'react';
import { motion } from 'framer-motion';

interface Avatar {
  id: string;
  name: string;
  emoji: string;
  description: string;
  voiceType: string;
  provider: string;
  languages: string[];
  gender: string;
}

const AVAILABLE_AVATARS: Avatar[] = [
  // English voices
  {
    id: 'rachel',
    name: 'Rachel',
    emoji: '👩',
    description: 'Warm and professional',
    voiceType: 'professional',
    provider: 'elevenlabs',
    languages: ['en'],
    gender: 'female'
  },
  {
    id: 'drew',
    name: 'Drew',
    emoji: '👨',
    description: 'Confident and clear',
    voiceType: 'confident',
    provider: 'elevenlabs',
    languages: ['en'],
    gender: 'male'
  },
  {
    id: 'thalia',
    name: 'Thalia',
    emoji: '🎭',
    description: 'Clear and energetic',
    voiceType: 'energetic',
    provider: 'deepgram',
    languages: ['en'],
    gender: 'female'
  },
  {
    id: 'apollo',
    name: 'Apollo',
    emoji: '🌟',
    description: 'Confident and casual',
    voiceType: 'casual',
    provider: 'deepgram',
    languages: ['en'],
    gender: 'male'
  },
  {
    id: 'john',
    name: 'John',
    emoji: '👨‍💼',
    description: 'Loud and clear',
    voiceType: 'clear',
    provider: 'spitch',
    languages: ['en'],
    gender: 'male'
  },
  {
    id: 'lucy',
    name: 'Lucy',
    emoji: '👩‍💼',
    description: 'Very clear voice',
    voiceType: 'clear',
    provider: 'spitch',
    languages: ['en'],
    gender: 'female'
  },
  // Spanish voices
  {
    id: 'celeste',
    name: 'Celeste',
    emoji: '🌺',
    description: 'Clear, energetic Colombian',
    voiceType: 'energetic',
    provider: 'deepgram',
    languages: ['es'],
    gender: 'female'
  },
  {
    id: 'nestor',
    name: 'Nestor',
    emoji: '🎩',
    description: 'Calm, professional Spanish',
    voiceType: 'professional',
    provider: 'deepgram',
    languages: ['es'],
    gender: 'male'
  },
  // Yoruba voices
  {
    id: 'sade',
    name: 'Sade',
    emoji: '👑',
    description: 'Energetic, but breezy',
    voiceType: 'energetic',
    provider: 'spitch',
    languages: ['yo'],
    gender: 'female'
  },
  {
    id: 'funmi',
    name: 'Funmi',
    emoji: '🌸',
    description: 'Calm, can be fun',
    voiceType: 'calm',
    provider: 'spitch',
    languages: ['yo'],
    gender: 'female'
  },
  {
    id: 'segun',
    name: 'Segun',
    emoji: '⚡',
    description: 'Vibrant, yet cool',
    voiceType: 'vibrant',
    provider: 'spitch',
    languages: ['yo'],
    gender: 'male'
  },
  {
    id: 'femi',
    name: 'Femi',
    emoji: '😄',
    description: 'Fun guy to interact with',
    voiceType: 'fun',
    provider: 'spitch',
    languages: ['yo'],
    gender: 'male'
  },
  // Hausa voices
  {
    id: 'hasan',
    name: 'Hasan',
    emoji: '🗣️',
    description: 'Loud and clear',
    voiceType: 'clear',
    provider: 'spitch',
    languages: ['ha'],
    gender: 'male'
  },
  {
    id: 'amina',
    name: 'Amina',
    emoji: '🌙',
    description: 'Quiet and soft',
    voiceType: 'soft',
    provider: 'spitch',
    languages: ['ha'],
    gender: 'female'
  },
  {
    id: 'zainab',
    name: 'Zainab',
    emoji: '💫',
    description: 'Clear, loud voice',
    voiceType: 'clear',
    provider: 'spitch',
    languages: ['ha'],
    gender: 'female'
  },
  {
    id: 'aliyu',
    name: 'Aliyu',
    emoji: '🌊',
    description: 'Soft voice, cool tone',
    voiceType: 'cool',
    provider: 'spitch',
    languages: ['ha'],
    gender: 'male'
  },
  // Igbo voices
  {
    id: 'obinna',
    name: 'Obinna',
    emoji: '🎯',
    description: 'Loud and clear',
    voiceType: 'clear',
    provider: 'spitch',
    languages: ['ig'],
    gender: 'male'
  },
  {
    id: 'ngozi',
    name: 'Ngozi',
    emoji: '🌺',
    description: 'Quiet and soft',
    voiceType: 'soft',
    provider: 'spitch',
    languages: ['ig'],
    gender: 'female'
  },
  {
    id: 'amara',
    name: 'Amara',
    emoji: '💎',
    description: 'Clear, loud voice',
    voiceType: 'clear',
    provider: 'spitch',
    languages: ['ig'],
    gender: 'female'
  },
  {
    id: 'ebuka',
    name: 'Ebuka',
    emoji: '🎭',
    description: 'Soft voice, cool tone',
    voiceType: 'cool',
    provider: 'spitch',
    languages: ['ig'],
    gender: 'male'
  },
  // French voice
  {
    id: 'pandora',
    name: 'Pandora',
    emoji: '🎨',
    description: 'Smooth, calm, melodic',
    voiceType: 'melodic',
    provider: 'deepgram',
    languages: ['fr'],
    gender: 'female'
  },
];

// Export for use in other components
export { AVAILABLE_AVATARS };

interface AvatarSelectorProps {
  selectedAvatar: string;
  selectedLanguage?: string;
  onAvatarChange: (avatarId: string) => void;
}

const AvatarSelector: React.FC<AvatarSelectorProps> = ({
  selectedAvatar,
  selectedLanguage = 'en',
  onAvatarChange,
}) => {
  // Filter avatars based on selected language
  const availableAvatars = AVAILABLE_AVATARS.filter(avatar => 
    avatar.languages.includes(selectedLanguage)
  );

  // If no avatars for selected language, show English as fallback
  const avatarsToShow = availableAvatars.length > 0 ? availableAvatars : 
    AVAILABLE_AVATARS.filter(avatar => avatar.languages.includes('en'));

  return (
    <div className="grid grid-cols-2 gap-3">
      {avatarsToShow.map((avatar) => (
        <motion.button
          key={avatar.id}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onAvatarChange(avatar.id)}
          className={`p-4 rounded-xl border-2 transition-all duration-200 ${
            selectedAvatar === avatar.id
              ? 'border-white bg-white/10 shadow-lg shadow-white/25 dark:border-white dark:bg-white/10'
              : 'border-black-700 bg-black-900 hover:border-black-600 hover:bg-black-800 dark:border-black-700 dark:bg-black-900 dark:hover:border-black-600 dark:hover:bg-black-800'
          }`}
        >
          <div className="text-center">
            <div className="text-2xl mb-2">{avatar.emoji}</div>
            <div className="text-white dark:text-white text-sm font-medium mb-1">{avatar.name}</div>
            <div className="text-dark-300 dark:text-dark-300 text-xs mb-2">{avatar.description}</div>
            <div className="flex justify-center">
              <span className={`text-xs px-2 py-1 rounded-full ${
                avatar.provider === 'spitch' ? 'bg-green-500/20 text-green-400' :
                avatar.provider === 'deepgram' ? 'bg-blue-500/20 text-blue-400' :
                'bg-purple-500/20 text-purple-400'
              }`}>
                {avatar.provider}
              </span>
            </div>
          </div>
        </motion.button>
      ))}
    </div>
  );
};

export default AvatarSelector;
