-- Supabase Database Setup for Translation Service
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

-- Create voice_avatars table (optional - for storing voice configurations)
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
CREATE INDEX IF NOT EXISTS idx_rooms_room_id ON rooms(room_id);
CREATE INDEX IF NOT EXISTS idx_rooms_active ON rooms(is_active);
CREATE INDEX IF NOT EXISTS idx_voice_avatars_language ON voice_avatars(language);

-- Insert default voice avatars
INSERT INTO voice_avatars (voice_id, provider, name, gender, accent, description, language) VALUES
-- English voices
('21m00Tcm4TlvDq8ikWAM', 'elevenlabs', 'Rachel', 'female', 'american', 'Warm and professional female voice', 'en'),
('29vD33N1CtxCmqQRPOHJ', 'elevenlabs', 'Drew', 'male', 'american', 'Confident and clear male voice', 'en'),

-- Igbo voices (placeholders - replace with actual ElevenLabs voices)
('ig_female_1', 'elevenlabs', 'Ada', 'female', 'nigerian', 'Native Igbo female voice', 'ig'),

-- Yoruba voices (placeholders - replace with actual ElevenLabs voices)
('yo_female_1', 'elevenlabs', 'Funmi', 'female', 'nigerian', 'Native Yoruba female voice', 'yo'),

-- Hausa voices (placeholders - replace with actual ElevenLabs voices)
('ha_female_1', 'elevenlabs', 'Amina', 'female', 'nigerian', 'Native Hausa female voice', 'ha')

ON CONFLICT (voice_id) DO NOTHING;

-- Enable Row Level Security (RLS) for security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_avatars ENABLE ROW LEVEL SECURITY;

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

-- Create triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
