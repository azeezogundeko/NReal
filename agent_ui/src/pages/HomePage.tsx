import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import LanguageSelector from '../components/LanguageSelector';
import AvatarSelector from '../components/AvatarSelector';
import TranslationRoomSetup from '../components/TranslationRoomSetup';
import { apiService } from '../services/api';

// Import the avatar data from the component
import { AVAILABLE_AVATARS } from '../components/AvatarSelector';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [roomId, setRoomId] = useState('');
  const [userName, setUserName] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [selectedAvatar, setSelectedAvatar] = useState('rachel');
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [isAvatarModalOpen, setIsAvatarModalOpen] = useState(false);
  const [isTranslationModalOpen, setIsTranslationModalOpen] = useState(false);

  // Update selected avatar when language changes
  useEffect(() => {
    const availableAvatarsForLanguage = AVAILABLE_AVATARS.filter(avatar => 
      avatar.languages.includes(selectedLanguage)
    );
    
    if (availableAvatarsForLanguage.length > 0) {
      // Check if current avatar is available for this language
      const currentAvatarAvailable = availableAvatarsForLanguage.some(avatar => avatar.id === selectedAvatar);
      
      if (!currentAvatarAvailable) {
        // Select the first available avatar for this language
        setSelectedAvatar(availableAvatarsForLanguage[0].id);
      }
    }
  }, [selectedLanguage, selectedAvatar]);

  const handleJoinRoom = () => {
    if (roomId.trim() && userName.trim()) {
      const params = new URLSearchParams({
        userName,
        language: selectedLanguage,
        avatar: selectedAvatar
      });
      navigate(`/room/${roomId}?${params.toString()}`);
    }
  };

  const handleCreateRoom = async () => {
    if (!userName.trim()) return;
    
    setIsCreatingRoom(true);
    
    try {
      // Create room via backend API
      const roomResponse = await apiService.createRoom({
        host_identity: userName,
        room_name: `${userName}'s Room`,
        max_participants: 50
      });

      if (roomResponse.success) {
        const params = new URLSearchParams({
          userName,
          language: selectedLanguage,
          avatar: selectedAvatar
        });
        
        // Use the room_name from the response for navigation
        navigate(`/room/${roomResponse.room.room_name}?${params.toString()}`);
      }
    } catch (error) {
      console.error('Failed to create room:', error);
      // Fallback to local room creation
      const newRoomId = `room-${Date.now()}`;
      const params = new URLSearchParams({
        userName,
        language: selectedLanguage,
        avatar: selectedAvatar
      });
      navigate(`/room/${newRoomId}?${params.toString()}`);
    } finally {
      setIsCreatingRoom(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black-950 via-black-900 to-black-950 flex items-center justify-center p-4 dark">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-6xl"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <motion.h1
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent"
          >
            Speech.app
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-dark-300 text-lg"
          >
            Real-time voice translation platform
          </motion.p>
        </div>

        {/* Main Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="glass-effect rounded-xl p-6 shadow-2xl max-w-sm mx-auto"
        >
          {/* User Name Input */}
          <div className="mb-4">
            <label className="block text-white text-sm font-medium mb-2">
              Your Name
            </label>
            <input
              type="text"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="Enter your name"
              className="w-full px-3 py-2.5 bg-black-900 border border-black-700 rounded-lg text-white placeholder-black-500 focus:outline-none focus:ring-2 focus:ring-black-600 focus:border-transparent transition-all dark:bg-black-900 dark:border-black-700 dark:text-white"
            />
          </div>

          {/* Language Selection */}
          <div className="mb-4">
            <label className="block text-white text-sm font-medium mb-2">
              Your Language
            </label>
            <LanguageSelector
              selectedLanguage={selectedLanguage}
              onLanguageChange={setSelectedLanguage}
            />
          </div>

          {/* Avatar Selection */}
          <div className="mb-4">
            <label className="block text-white text-sm font-medium mb-2">
              Choose Avatar
            </label>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setIsAvatarModalOpen(true)}
              className="w-full p-3 bg-black-900 border border-black-700 rounded-lg hover:bg-black-800 hover:border-black-600 transition-all duration-200 flex items-center justify-between"
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-xl border border-white/20">
                  {AVAILABLE_AVATARS.find(a => a.id === selectedAvatar)?.emoji || '👤'}
                </div>
                <div className="text-left">
                  <div className="text-white font-medium">
                    {AVAILABLE_AVATARS.find(a => a.id === selectedAvatar)?.name || 'Alex'}
                  </div>
                  <div className="text-white/70 text-sm">
                    {AVAILABLE_AVATARS.find(a => a.id === selectedAvatar)?.description || 'Neutral voice'}
                  </div>
                </div>
              </div>
              <svg className="w-5 h-5 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </motion.button>
          </div>

          {/* Room Controls */}
          <div className="space-y-4">
            {/* Join Room */}
            <div>
              <input
                type="text"
                value={roomId}
                onChange={(e) => setRoomId(e.target.value)}
                placeholder="Enter room ID to join"
                className="w-full px-3 py-2.5 bg-black-900 border border-black-700 rounded-lg text-white placeholder-black-500 focus:outline-none focus:ring-2 focus:ring-black-600 focus:border-transparent transition-all mb-3 dark:bg-black-900 dark:border-black-700 dark:text-white"
              />
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleJoinRoom}
                disabled={!roomId.trim() || !userName.trim()}
                className="w-full py-2.5 bg-primary-600 hover:bg-primary-700 disabled:bg-dark-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all duration-200 flex items-center justify-center"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                Join Room
              </motion.button>
            </div>

            {/* Divider */}
            <div className="flex items-center">
              <div className="flex-1 border-t border-dark-600"></div>
              <span className="px-4 text-dark-400 text-sm">or</span>
              <div className="flex-1 border-t border-dark-600"></div>
            </div>

            {/* Create Room */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleCreateRoom}
              disabled={!userName.trim() || isCreatingRoom}
              className="w-full py-2.5 bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 disabled:from-dark-600 disabled:to-dark-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all duration-200 flex items-center justify-center"
            >
              {isCreatingRoom ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating Room...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Create New Room
                </>
              )}
            </motion.button>

            {/* Translation Room */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setIsTranslationModalOpen(true)}
              className="w-full py-2.5 bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 text-white font-medium rounded-lg transition-all duration-200 flex items-center justify-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
              🌐 Create Translation Room
            </motion.button>
          </div>
        </motion.div>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-8 text-center"
        >
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm text-dark-300">
            <div className="flex items-center justify-center">
              <svg className="w-4 h-4 mr-2 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
              </svg>
              Real-time Voice
            </div>
            <div className="flex items-center justify-center">
              <svg className="w-4 h-4 mr-2 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.578a18.87 18.87 0 01-1.724 4.78c.29.354.596.696.914 1.026a1 1 0 11-1.44 1.389c-.188-.196-.373-.396-.554-.6a19.098 19.098 0 01-3.107 3.567 1 1 0 01-1.334-1.49 17.087 17.087 0 003.13-3.733 18.992 18.992 0 01-1.487-2.494 1 1 0 111.79-.89c.234.47.489.928.764 1.372.417-.934.752-1.913.997-2.927H3a1 1 0 110-2h3V3a1 1 0 011-1zm6 6a1 1 0 01.894.553l2.991 5.982a.869.869 0 01.02.037l.99 1.98a1 1 0 11-1.79.895L15.383 16h-4.764l-.724 1.447a1 1 0 11-1.788-.894l.99-1.98.019-.038 2.99-5.982A1 1 0 0113 8zm-1.382 6h2.764L13 11.236 11.618 14z" clipRule="evenodd" />
              </svg>
              500ms Translation
            </div>
            <div className="flex items-center justify-center">
              <svg className="w-4 h-4 mr-2 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
              </svg>
              Voice Avatars
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Avatar Selection Modal */}
      <AnimatePresence>
        {isAvatarModalOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => setIsAvatarModalOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="glass-effect rounded-2xl p-8 shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Choose Your Avatar</h2>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsAvatarModalOpen(false)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </motion.button>
            </div>

            {/* Avatar Grid */}
            <div className="mb-6">
              <AvatarSelector
                selectedAvatar={selectedAvatar}
                selectedLanguage={selectedLanguage}
                onAvatarChange={(avatarId) => {
                  setSelectedAvatar(avatarId);
                  setIsAvatarModalOpen(false);
                }}
              />
            </div>

            {/* Selected Avatar Preview */}
            <div className="text-center p-4 bg-white/5 rounded-lg">
              {(() => {
                const selectedAvatarData = AVAILABLE_AVATARS.find(a => a.id === selectedAvatar);
                return selectedAvatarData ? (
                  <>
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-white/10 flex items-center justify-center text-3xl border-2 border-white/20">
                      {selectedAvatarData.emoji}
                    </div>
                    <h3 className="text-white font-medium text-lg mb-1">
                      {selectedAvatarData.name}
                    </h3>
                    <p className="text-white/70 text-sm mb-2">
                      {selectedAvatarData.description}
                    </p>
                    <div className="flex justify-center space-x-2">
                      <div className="px-3 py-1 bg-white/10 rounded-full">
                        <span className="text-white/80 text-xs font-medium">
                          {selectedAvatarData.voiceType} voice
                        </span>
                      </div>
                      <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                        selectedAvatarData.provider === 'spitch' ? 'bg-green-500/20 text-green-400' :
                        selectedAvatarData.provider === 'deepgram' ? 'bg-blue-500/20 text-blue-400' :
                        'bg-purple-500/20 text-purple-400'
                      }`}>
                        {selectedAvatarData.provider}
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-white/10 flex items-center justify-center text-3xl border-2 border-white/20">
                      👤
                    </div>
                    <h3 className="text-white font-medium text-lg mb-1">Default</h3>
                    <p className="text-white/70 text-sm mb-2">Select an avatar</p>
                  </>
                );
              })()}
            </div>

            {/* Modal Footer */}
            <div className="mt-6 flex justify-end">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setIsAvatarModalOpen(false)}
                className="px-6 py-2 bg-white text-black font-medium rounded-lg hover:bg-white/90 transition-colors"
              >
                Done
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
        )}
      </AnimatePresence>

      {/* Translation Room Modal */}
      <AnimatePresence>
        {isTranslationModalOpen && (
          <TranslationRoomSetup onClose={() => setIsTranslationModalOpen(false)} />
        )}
      </AnimatePresence>
    </div>
  );
};

export default HomePage;
