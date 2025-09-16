-- Complete Database Setup for Translation Service
-- Run these SQL commands in your Supabase SQL editor

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_identity VARCHAR(255) UNIQUE NOT NULL,
    native_language VARCHAR(10) NOT NULL DEFAULT 'en',
    voice_avatar_id VARCHAR(255),
    voice_provider VARCHAR(50) DEFAULT 'elevenlabs',
    formal_tone BOOLEAN DEFAULT FALSE,
    preserve_emotion BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(255) UNIQUE NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    host_identity VARCHAR(255) NOT NULL,
    max_participants INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create voice_avatars table
CREATE TABLE IF NOT EXISTS voice_avatars (
    id SERIAL PRIMARY KEY,
    voice_id VARCHAR(255) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(20) NOT NULL,
    accent VARCHAR(50) NOT NULL,
    description TEXT,
    language VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_identity ON user_profiles(user_identity);
CREATE INDEX IF NOT EXISTS idx_user_profiles_language ON user_profiles(native_language);
CREATE INDEX IF NOT EXISTS idx_rooms_room_id ON rooms(room_id);
CREATE INDEX IF NOT EXISTS idx_rooms_active ON rooms(is_active);
CREATE INDEX IF NOT EXISTS idx_rooms_host ON rooms(host_identity);
CREATE INDEX IF NOT EXISTS idx_voice_avatars_language ON voice_avatars(language);
CREATE INDEX IF NOT EXISTS idx_voice_avatars_provider ON voice_avatars(provider);

-- Insert default voice avatars
INSERT INTO voice_avatars (voice_id, provider, name, gender, accent, description, language) VALUES
-- ElevenLabs English voices
('21m00Tcm4TlvDq8ikWAM', 'elevenlabs', 'Rachel', 'female', 'american', 'Warm and professional female voice', 'en'),
('29vD33N1CtxCmqQRPOHJ', 'elevenlabs', 'Drew', 'male', 'american', 'Confident and clear male voice', 'en'),

-- OpenAI English voices (from frontend api.ts)
('alloy', 'openai', 'Alex', 'neutral', 'american', 'Default balanced voice', 'en'),
('echo', 'openai', 'Professional', 'male', 'american', 'Professional male voice', 'en'),
('fable', 'openai', 'Friendly', 'male', 'american', 'Friendly conversational voice', 'en'),
('onyx', 'openai', 'Confident', 'male', 'american', 'Confident authoritative voice', 'en'),
('nova', 'openai', 'Gentle', 'female', 'american', 'Gentle caring voice', 'en'),
('shimmer', 'openai', 'Energetic', 'female', 'american', 'Energetic enthusiastic voice', 'en'),

-- Nigerian language voices (placeholders - replace with actual voice IDs when available)
('ig_female_1', 'elevenlabs', 'Ada', 'female', 'nigerian', 'Native Igbo female voice', 'ig'),
('ig_male_1', 'elevenlabs', 'Emeka', 'male', 'nigerian', 'Native Igbo male voice', 'ig'),

('yo_female_1', 'elevenlabs', 'Funmi', 'female', 'nigerian', 'Native Yoruba female voice', 'yo'),
('yo_male_1', 'elevenlabs', 'Adebayo', 'male', 'nigerian', 'Native Yoruba male voice', 'yo'),

('ha_female_1', 'elevenlabs', 'Amina', 'female', 'nigerian', 'Native Hausa female voice', 'ha'),
('ha_male_1', 'elevenlabs', 'Ibrahim', 'male', 'nigerian', 'Native Hausa male voice', 'ha')

ON CONFLICT (voice_id) DO NOTHING;

-- Enable Row Level Security (RLS) for security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_avatars ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Users can view their own profiles" ON user_profiles;
DROP POLICY IF EXISTS "Users can insert their own profiles" ON user_profiles;
DROP POLICY IF EXISTS "Users can update their own profiles" ON user_profiles;
DROP POLICY IF EXISTS "Users can view active rooms" ON rooms;
DROP POLICY IF EXISTS "Users can create rooms" ON rooms;
DROP POLICY IF EXISTS "Room hosts can update their rooms" ON rooms;
DROP POLICY IF EXISTS "Authenticated users can view voice avatars" ON voice_avatars;

-- Create policies for user_profiles (users can only access their own profiles)
CREATE POLICY "Users can view their own profiles" ON user_profiles
    FOR SELECT USING (auth.uid()::text = user_identity);

CREATE POLICY "Users can insert their own profiles" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid()::text = user_identity);

CREATE POLICY "Users can update their own profiles" ON user_profiles
    FOR UPDATE USING (auth.uid()::text = user_identity);

-- Create policies for rooms (more permissive for room access)
CREATE POLICY "Users can view active rooms" ON rooms
    FOR SELECT USING (is_active = true);

CREATE POLICY "Users can create rooms" ON rooms
    FOR INSERT WITH CHECK (auth.uid()::text = host_identity);

CREATE POLICY "Room hosts can update their rooms" ON rooms
    FOR UPDATE USING (auth.uid()::text = host_identity);

-- Create policies for voice_avatars (read-only for all authenticated users)
CREATE POLICY "Authenticated users can view voice avatars" ON voice_avatars
    FOR SELECT USING (auth.role() = 'authenticated');

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
DROP TRIGGER IF EXISTS update_rooms_updated_at ON rooms;

-- Create triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a view for active rooms with host information (optional)
CREATE OR REPLACE VIEW active_rooms_with_host AS
SELECT 
    r.id,
    r.room_id,
    r.room_name,
    r.host_identity,
    r.max_participants,
    r.created_at,
    up.native_language as host_language,
    up.voice_provider as host_voice_provider
FROM rooms r
LEFT JOIN user_profiles up ON r.host_identity = up.user_identity
WHERE r.is_active = true;

-- Create a function to clean up old inactive rooms (optional)
CREATE OR REPLACE FUNCTION cleanup_old_rooms(days_old INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM rooms 
    WHERE is_active = false 
    AND updated_at < NOW() - INTERVAL '1 day' * days_old;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT USAGE ON SCHEMA public TO anon, authenticated;
-- GRANT SELECT ON user_profiles TO authenticated;
-- GRANT INSERT, UPDATE ON user_profiles TO authenticated;
-- GRANT SELECT ON rooms TO authenticated;
-- GRANT INSERT, UPDATE ON rooms TO authenticated;
-- GRANT SELECT ON voice_avatars TO authenticated;

-- Create some sample data for testing (optional - remove in production)
-- INSERT INTO user_profiles (user_identity, native_language, voice_avatar_id, voice_provider) VALUES
-- ('test_user_1', 'en', 'alloy', 'openai'),
-- ('test_user_2', 'ig', 'ig_female_1', 'elevenlabs')
-- ON CONFLICT (user_identity) DO NOTHING;

-- Verification queries (run these to verify your setup)
-- SELECT 'user_profiles' as table_name, count(*) as row_count FROM user_profiles
-- UNION ALL
-- SELECT 'rooms' as table_name, count(*) as row_count FROM rooms
-- UNION ALL
-- SELECT 'voice_avatars' as table_name, count(*) as row_count FROM voice_avatars;

-- Show available voice avatars by language
-- SELECT language, count(*) as voice_count, string_agg(name, ', ') as available_voices
-- FROM voice_avatars 
-- GROUP BY language 
-- ORDER BY language;
