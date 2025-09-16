/**
 * API service for backend communication
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface TokenRequest {
  user_identity: string;
  room_name: string;
  user_metadata?: {
    name?: string;
    language?: string;
    avatar?: string;
    room_type?: string;
  };
}

export interface TokenResponse {
  token: string;
  ws_url: string;
  room_name: string;
  user_profile: {
    user_identity: string;
    native_language: string;
    voice_avatar: {
      voice_id: string;
      provider: string;
      name: string;
    };
    translation_preferences: any;
  };
}

export interface CreateRoomRequest {
  host_identity: string;
  room_name?: string;
  max_participants?: number;
}

export interface CreateRoomResponse {
  success: boolean;
  room: {
    room_id: string;
    room_name: string;
    join_url: string;
    max_participants?: number;
    host_profile?: {
      user_identity: string;
      native_language: string;
    };
  };
}

export interface UserProfile {
  user_identity: string;
  native_language: string;
  preferred_voice_avatar: {
    voice_id: string;
    provider: string;
    name: string;
  };
  translation_preferences: any;
}

export interface CreateProfileRequest {
  user_identity: string;
  native_language?: string;
  preferred_voice_avatar?: {
    voice_id: string;
    provider: string;
    name: string;
  };
  translation_preferences?: {
    formal_tone: boolean;
    preserve_emotion: boolean;
  };
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}/api${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  /**
   * Generate LiveKit access token
   */
  async generateToken(request: TokenRequest): Promise<TokenResponse> {
    return this.request<TokenResponse>('/token/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Create a new room
   */
  async createRoom(request: CreateRoomRequest): Promise<CreateRoomResponse> {
    return this.request<CreateRoomResponse>('/rooms/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get user profile
   */
  async getUserProfile(userIdentity: string): Promise<UserProfile> {
    return this.request<UserProfile>(`/profiles/${encodeURIComponent(userIdentity)}`);
  }

  /**
   * Create user profile
   */
  async createUserProfile(request: CreateProfileRequest): Promise<UserProfile> {
    return this.request<UserProfile>('/profiles/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get or create user profile
   */
  async getOrCreateUserProfile(
    userIdentity: string, 
    language: string = 'en',
    avatar: string = 'default'
  ): Promise<UserProfile> {
    try {
      // Try to get existing profile
      return await this.getUserProfile(userIdentity);
    } catch (error) {
      // If profile doesn't exist, create it
      console.log(`Creating new profile for user: ${userIdentity}`);
      
      // Map avatar to voice avatar based on language and avatar selection
      const voiceAvatarMap: Record<string, any> = {
        // English voices
        rachel: { voice_id: '21m00Tcm4TlvDq8ikWAM', provider: 'elevenlabs', model: 'eleven_turbo_v2_5', name: 'Rachel' },
        drew: { voice_id: '29vD33N1CtxCmqQRPOHJ', provider: 'elevenlabs', model: 'eleven_turbo_v2_5', name: 'Drew' },
        thalia: { voice_id: 'aura-2-thalia-en', provider: 'deepgram', model: 'aura-2-thalia-en', name: 'Thalia' },
        apollo: { voice_id: 'aura-2-apollo-en', provider: 'deepgram', model: 'aura-2-apollo-en', name: 'Apollo' },
        john: { voice_id: 'John', provider: 'spitch', model: 'spitch-tts', name: 'John' },
        lucy: { voice_id: 'Lucy', provider: 'spitch', model: 'spitch-tts', name: 'Lucy' },
        lina: { voice_id: 'Lina', provider: 'spitch', model: 'spitch-tts', name: 'Lina' },
        jude: { voice_id: 'Jude', provider: 'spitch', model: 'spitch-tts', name: 'Jude' },
        henry: { voice_id: 'Henry', provider: 'spitch', model: 'spitch-tts', name: 'Henry' },
        kani: { voice_id: 'Kani', provider: 'spitch', model: 'spitch-tts', name: 'Kani' },
        
        // Spanish voices
        celeste: { voice_id: 'aura-2-celeste-es', provider: 'deepgram', model: 'aura-2-celeste-es', name: 'Celeste' },
        nestor: { voice_id: 'aura-2-nestor-es', provider: 'deepgram', model: 'aura-2-nestor-es', name: 'Nestor' },
        
        // Yoruba voices
        sade: { voice_id: 'Sade', provider: 'spitch', model: 'spitch-tts', name: 'Sade' },
        funmi: { voice_id: 'Funmi', provider: 'spitch', model: 'spitch-tts', name: 'Funmi' },
        segun: { voice_id: 'Segun', provider: 'spitch', model: 'spitch-tts', name: 'Segun' },
        femi: { voice_id: 'Femi', provider: 'spitch', model: 'spitch-tts', name: 'Femi' },
        
        // Hausa voices
        hasan: { voice_id: 'Hasan', provider: 'spitch', model: 'spitch-tts', name: 'Hasan' },
        amina: { voice_id: 'Amina', provider: 'spitch', model: 'spitch-tts', name: 'Amina' },
        zainab: { voice_id: 'Zainab', provider: 'spitch', model: 'spitch-tts', name: 'Zainab' },
        aliyu: { voice_id: 'Aliyu', provider: 'spitch', model: 'spitch-tts', name: 'Aliyu' },
        
        // Igbo voices
        obinna: { voice_id: 'Obinna', provider: 'spitch', model: 'spitch-tts', name: 'Obinna' },
        ngozi: { voice_id: 'Ngozi', provider: 'spitch', model: 'spitch-tts', name: 'Ngozi' },
        amara: { voice_id: 'Amara', provider: 'spitch', model: 'spitch-tts', name: 'Amara' },
        ebuka: { voice_id: 'Ebuka', provider: 'spitch', model: 'spitch-tts', name: 'Ebuka' },
        
        // French voices
        pandora: { voice_id: 'aura-2-pandora-en', provider: 'deepgram', model: 'aura-2-pandora-en', name: 'Pandora' },
        
        // Legacy fallbacks
        default: { voice_id: '21m00Tcm4TlvDq8ikWAM', provider: 'elevenlabs', model: 'eleven_turbo_v2_5', name: 'Rachel' },
        professional: { voice_id: 'aura-2-thalia-en', provider: 'deepgram', model: 'aura-2-thalia-en', name: 'Thalia' },
        friendly: { voice_id: 'Lucy', provider: 'spitch', model: 'spitch-tts', name: 'Lucy' },
        confident: { voice_id: '29vD33N1CtxCmqQRPOHJ', provider: 'elevenlabs', model: 'eleven_turbo_v2_5', name: 'Drew' },
        gentle: { voice_id: 'aura-2-pandora-en', provider: 'deepgram', model: 'aura-2-pandora-en', name: 'Pandora' },
        energetic: { voice_id: 'aura-2-apollo-en', provider: 'deepgram', model: 'aura-2-apollo-en', name: 'Apollo' },
      };

      const createRequest: CreateProfileRequest = {
        user_identity: userIdentity,
        native_language: language,
        preferred_voice_avatar: voiceAvatarMap[avatar] || voiceAvatarMap.default,
        translation_preferences: { formal_tone: false, preserve_emotion: true }
      };

      return await this.createUserProfile(createRequest);
    }
  }

  /**
   * Dispatch translation agent to a room
   */
  async dispatchAgentToRoom(roomName: string, userIdentity?: string): Promise<{
    success: boolean;
    message: string;
    dispatch_info: any;
  }> {
    const endpoint = `/rooms/${encodeURIComponent(roomName)}/dispatch-agent`;
    const url = userIdentity ? `${endpoint}?user_identity=${encodeURIComponent(userIdentity)}` : endpoint;
    
    return this.request(url, {
      method: 'POST',
    });
  }

  /**
   * List agent dispatches for a room
   */
  async listRoomDispatches(roomName: string): Promise<{
    success: boolean;
    room_name: string;
    dispatches: any[];
  }> {
    return this.request(`/rooms/${encodeURIComponent(roomName)}/dispatches`);
  }

  /**
   * Create a real-time translation room (2-user simultaneous interpretation)
   */
  async createTranslationRoom(
    hostIdentity: string,
    hostLanguage: string,
    participantBIdentity: string,
    participantBLanguage: string,
    roomName?: string
  ): Promise<{
    room: {
      room_id: string;
      room_name: string;
      room_type: string;
      max_participants: number;
      join_url: string;
    };
    participants: {
      host: {
        identity: string;
        language: string;
        token: string;
        ws_url: string;
      };
      participant_b: {
        identity: string;
        language: string;
        token: string;
        ws_url: string;
      };
    };
    translation_config: {
      max_delay_ms: number;
      interim_results: boolean;
      utterance_end_ms: number;
      audio_routing: boolean;
    };
  }> {
    return this.request('/realtime-translation/rooms/create', {
      method: 'POST',
      body: JSON.stringify({
        host_identity: hostIdentity,
        host_language: hostLanguage,
        participant_b_identity: participantBIdentity,
        participant_b_language: participantBLanguage,
        room_name: roomName,
      }),
    });
  }

  /**
   * Get real-time translation statistics for a room
   */
  async getTranslationRoomStats(roomId: string): Promise<{
    room_id: string;
    room_name: string;
    is_active: boolean;
    translation_stats: any;
    performance: {
      target_delay_ms: number;
      audio_routing_enabled: boolean;
      interim_results_enabled: boolean;
    };
  }> {
    return this.request(`/realtime-translation/rooms/${encodeURIComponent(roomId)}/stats`);
  }

  /**
   * Create a test translation setup (Spanish <-> English)
   */
  async createTestTranslationSetup(): Promise<{
    message: string;
    room: {
      room_id: string;
      room_name: string;
      join_url: string;
    };
    spanish_user: {
      identity: string;
      language: string;
      token: string;
      ws_url: string;
    };
    english_user: {
      identity: string;
      language: string;
      token: string;
      ws_url: string;
    };
    instructions: {
      spanish_user: string;
      english_user: string;
      features: string[];
    };
  }> {
    return this.request('/realtime-translation/test-setup', {
      method: 'POST',
    });
  }

  /**
   * Get real-time translation configuration
   */
  async getTranslationConfig(): Promise<{
    max_delay_ms: number;
    interim_results: boolean;
    utterance_end_ms: number;
    punctuate: boolean;
    smart_format: boolean;
    profanity_filter: boolean;
    redact: boolean;
    diarize: boolean;
    tier: string;
    detect_language: boolean;
    confidence_threshold: number;
    audio_routing: boolean;
    vad_enabled: boolean;
    supported_languages: string[];
    description: string;
  }> {
    return this.request('/realtime-translation/config');
  }

  /**
   * Create a translation room using the dedicated translation-rooms endpoint
   */
  async createTranslationRoomNew(request: {
    user_a_identity: string;
    user_a_language: string;
    user_a_name: string;
    user_b_identity: string;
    user_b_language: string;
    user_b_name: string;
    room_name?: string;
  }): Promise<{
    success: boolean;
    room: {
      room_name: string;
      room_id: string;
      room_type: string;
      max_participants: number;
    };
    user_a: {
      identity: string;
      name: string;
      language: string;
      token: string;
      server_url: string;
    };
    user_b: {
      identity: string;
      name: string;
      language: string;
      token: string;
      server_url: string;
    };
    instructions: {
      user_a: string;
      user_b: string;
      note: string;
    };
  }> {
    return this.request('/translation-rooms/create', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Join an existing translation room
   */
  async joinTranslationRoom(request: {
    room_name: string;
    user_identity: string;
    user_language: string;
    user_name: string;
  }): Promise<{
    success: boolean;
    user: {
      identity: string;
      name: string;
      language: string;
      token: string;
      server_url: string;
    };
    room: {
      room_name: string;
      room_type: string;
    };
  }> {
    return this.request('/translation-rooms/join', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Create a test translation room (English and Spanish users)
   */
  async createTestTranslationRoom(): Promise<{
    success: boolean;
    room: {
      room_name: string;
      room_id: string;
      room_type: string;
      max_participants: number;
    };
    user_a: {
      identity: string;
      name: string;
      language: string;
      token: string;
      server_url: string;
    };
    user_b: {
      identity: string;
      name: string;
      language: string;
      token: string;
      server_url: string;
    };
    instructions: {
      user_a: string;
      user_b: string;
      note: string;
    };
    testing_instructions: {
      step_1: string;
      step_2: string;
      step_3: string;
      step_4: string;
      expected_behavior: string;
    };
  }> {
    return this.request('/translation-rooms/test-room', {
      method: 'GET',
    });
  }
}

// Export singleton instance
export const apiService = new ApiService();
