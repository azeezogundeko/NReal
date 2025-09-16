import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { apiService } from '../services/api';

interface TranslationRoomSetupProps {
  onClose: () => void;
}

const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
];

const TranslationRoomSetup: React.FC<TranslationRoomSetupProps> = ({ onClose }) => {
  const navigate = useNavigate();
  const [step, setStep] = useState<'setup' | 'creating' | 'ready'>('setup');
  const [formData, setFormData] = useState({
    hostIdentity: '',
    hostLanguage: 'es',
    roomName: '',
  });
  const [roomData, setRoomData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleCreateRoom = async () => {
    if (!formData.hostIdentity.trim()) {
      setError('Host identity is required');
      return;
    }

    setStep('creating');
    setError(null);

    try {
      // Create a translation room using the dedicated translation-rooms endpoint
      // For now, we'll create a room for the host and a placeholder for the second user
      const response = await apiService.createTranslationRoomNew({
        user_a_identity: formData.hostIdentity,
        user_a_language: formData.hostLanguage,
        user_a_name: formData.hostIdentity,
        user_b_identity: `guest_${Date.now()}`, // Placeholder for the second user
        user_b_language: formData.hostLanguage === 'en' ? 'es' : 'en', // Default opposite language
        user_b_name: 'Guest User',
        room_name: formData.roomName || `Translation-${formData.hostIdentity}`
      });

      setRoomData({
        room: response.room,
        hostLanguage: formData.hostLanguage,
        hostIdentity: formData.hostIdentity,
        hostToken: response.user_a.token,
        hostServerUrl: response.user_a.server_url
      });
      setStep('ready');
    } catch (err: any) {
      setError(err.message || 'Failed to create translation room');
      setStep('setup');
    }
  };

  const handleJoinAsHost = () => {
    if (!roomData) return;
    
    // Store translation room data for the room page to use
    if (roomData.hostToken && roomData.hostServerUrl) {
      sessionStorage.setItem('translationRoomData', JSON.stringify({
        token: roomData.hostToken,
        wsUrl: roomData.hostServerUrl,
        roomName: roomData.room.room_name,
        userIdentity: roomData.hostIdentity,
        language: roomData.hostLanguage
      }));
    }
    
    const params = new URLSearchParams({
      userName: roomData.hostIdentity,
      language: roomData.hostLanguage,
      translationMode: 'true',
    });

    navigate(`/room/${roomData.room.room_name}?${params.toString()}`);
  };

  const handleTestSetup = async () => {
    setStep('creating');
    setError(null);

    try {
      const response = await apiService.createTestTranslationRoom();
      
      // Transform the response to match our expected format
      const transformedData = {
        room: response.room,
        hostLanguage: response.user_a.language,
        hostIdentity: response.user_a.identity,
        hostToken: response.user_a.token,
        hostServerUrl: response.user_a.server_url,
        participants: {
          host: {
            identity: response.user_a.identity,
            language: response.user_a.language,
            token: response.user_a.token,
            ws_url: response.user_a.server_url,
          },
          participant_b: {
            identity: response.user_b.identity,
            language: response.user_b.language,
            token: response.user_b.token,
            ws_url: response.user_b.server_url,
          },
        },
        instructions: response.instructions,
        testing_instructions: response.testing_instructions,
      };

      setRoomData(transformedData);
      setStep('ready');
    } catch (err: any) {
      setError(err.message || 'Failed to create test setup');
      setStep('setup');
    }
  };

  const getLanguageName = (code: string) => {
    return SUPPORTED_LANGUAGES.find(lang => lang.code === code)?.name || code;
  };

  const getLanguageFlag = (code: string) => {
    return SUPPORTED_LANGUAGES.find(lang => lang.code === code)?.flag || '🌐';
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-gray-900 rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-gray-700"
      >
        {step === 'setup' && (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">
                🌐 Create Translation Room
              </h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-6">
              <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-blue-300 mb-2">
                  ⚡ Real-Time Simultaneous Interpretation
                </h3>
                <ul className="text-sm text-blue-200 space-y-1">
                  <li>• 500ms max translation delay</li>
                  <li>• No audio pollution - clean routing</li>
                  <li>• User A speaks Spanish → User B hears English</li>
                  <li>• User B speaks English → User A hears Spanish</li>
                </ul>
              </div>

              {/* Quick Test Setup */}
              <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-green-300 mb-2">
                  🧪 Quick Test Setup
                </h3>
                <p className="text-sm text-green-200 mb-3">
                  Create a ready-to-use Spanish ↔ English translation room
                </p>
                <button
                  onClick={handleTestSetup}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  Create Test Room
                </button>
              </div>

              <div className="border-t border-gray-700 pt-6">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Custom Translation Room
                </h3>

                {/* Room Name */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Room Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.roomName}
                    onChange={(e) => handleInputChange('roomName', e.target.value)}
                    placeholder="My Translation Room"
                    className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
                  />
                </div>

                {/* Host Configuration */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Your Name
                    </label>
                    <input
                      type="text"
                      value={formData.hostIdentity}
                      onChange={(e) => handleInputChange('hostIdentity', e.target.value)}
                      placeholder="Your name"
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Your Language
                    </label>
                    <select
                      value={formData.hostLanguage}
                      onChange={(e) => handleInputChange('hostLanguage', e.target.value)}
                      className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:border-blue-500 focus:outline-none"
                    >
                      {SUPPORTED_LANGUAGES.map(lang => (
                        <option key={lang.code} value={lang.code}>
                          {lang.flag} {lang.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {error && (
                  <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3 mb-4">
                    <p className="text-red-300 text-sm">{error}</p>
                  </div>
                )}

                <button
                  onClick={handleCreateRoom}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium transition-colors"
                >
                  Create Translation Room
                </button>
              </div>
            </div>
          </>
        )}

        {step === 'creating' && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Creating Translation Room...
            </h2>
            <p className="text-gray-400">
              Setting up real-time simultaneous interpretation
            </p>
          </div>
        )}

        {step === 'ready' && roomData && (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">
                ✅ Translation Room Created
              </h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-6">
              <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-green-300 mb-2">
                  🎯 Room: {roomData.room.room_name}
                </h3>
                <p className="text-sm text-green-200">
                  Real-time translation room ready - share the Room ID with the other person
                </p>
              </div>

              {/* Room ID for sharing */}
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
                <h4 className="font-semibold text-white mb-3">📱 Share this Room ID</h4>
                <div className="flex items-center justify-between bg-gray-700 rounded-lg p-3">
                  <code className="text-blue-400 font-mono text-lg">{roomData.room.room_name}</code>
                  <button
                    onClick={() => navigator.clipboard.writeText(roomData.room.room_name)}
                    className="ml-3 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
                  >
                    Copy
                  </button>
                </div>
                <p className="text-sm text-gray-400 mt-2">
                  The other person should enter this Room ID to join the translation session
                </p>
              </div>

              {/* Host join button */}
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
                <div className="flex items-center mb-3">
                  <span className="text-2xl mr-2">
                    {getLanguageFlag(roomData.hostLanguage)}
                  </span>
                  <div>
                    <h4 className="font-semibold text-white">
                      {roomData.hostIdentity} (You)
                    </h4>
                    <p className="text-sm text-gray-400">
                      Speaks {getLanguageName(roomData.hostLanguage)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleJoinAsHost}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  Join Translation Room
                </button>
              </div>

              <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                <h4 className="font-semibold text-blue-300 mb-2">How it works:</h4>
                <ul className="text-sm text-blue-200 space-y-1">
                  <li>• You speak {getLanguageName(roomData.hostLanguage)} → Other person hears it translated</li>
                  <li>• Other person speaks their language → You hear it in {getLanguageName(roomData.hostLanguage)}</li>
                  <li>• No audio pollution - each person only hears the other in their preferred language</li>
                  <li>• Ultra-fast translation with 500ms max delay</li>
                </ul>
              </div>

              <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
                <h4 className="font-semibold text-yellow-300 mb-2">💡 Instructions:</h4>
                <ol className="text-sm text-yellow-200 space-y-1">
                  <li>1. Share the Room ID with the other person</li>
                  <li>2. They should enter the Room ID on the home page to join</li>
                  <li>3. Both of you click "Join" when ready</li>
                  <li>4. Allow microphone access when prompted</li>
                  <li>5. Start speaking naturally - translation happens automatically</li>
                </ol>
              </div>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
};

export default TranslationRoomSetup;
