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
}

// Export singleton instance
export const apiService = new ApiService();
