# Real-Time Translation Architecture Fix

## Current Problem
The second user's audio is not being properly processed for translation because:

1. **Frontend Architecture Issue**: Using single-user voice agent setup instead of multi-user translation room
2. **Audio Routing Issue**: Agents are hearing their own TTS output creating feedback loops
3. **Token/Permission Issue**: Not properly configured for peer-to-peer audio transmission

## Required Architecture

### 1. Frontend Changes Needed

#### A. Create Multi-User Translation Room Component
```typescript
// New component: TranslationRoom.tsx
interface TranslationRoomProps {
  userA: { identity: string; language: string; token: string };
  userB: { identity: string; language: string; token: string };
  roomName: string;
}

export function TranslationRoom({ userA, userB, roomName }: TranslationRoomProps) {
  // Connect both users to the same room
  // Enable microphone for both users
  // Set up proper audio routing
}
```

#### B. Audio Track Management
```typescript
// Enable microphone and ensure audio publishing
useEffect(() => {
  const enableAudio = async () => {
    if (localParticipant && connectionState === ConnectionState.Connected) {
      try {
        // Ensure microphone is enabled and publishing
        await localParticipant.setMicrophoneEnabled(true);
        console.log('Microphone enabled and publishing');
      } catch (error) {
        console.error('Failed to enable microphone:', error);
      }
    }
  };
  
  enableAudio();
}, [localParticipant, connectionState]);
```

### 2. Backend Changes Needed

#### A. Agent Audio Filtering
```python
# In agents, filter out own TTS to prevent feedback
async def start(self, ctx: JobContext):
    # Connect with audio subscription but filter own output
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Set up audio filtering to ignore own TTS output
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        # Only process audio from OTHER participants
        if participant.identity != self.user_profile.user_identity:
            # Process this audio for translation
            pass
```

#### B. Proper Agent Dispatch
```python
# Create separate agents for each user
room_config = api.RoomConfiguration(
    agents=[
        api.RoomAgentDispatch(
            agent_name="translation-agent",
            metadata=json.dumps({
                "target_user": user_a_identity,
                "source_language": user_b_language,
                "target_language": user_a_language
            })
        ),
        api.RoomAgentDispatch(
            agent_name="translation-agent", 
            metadata=json.dumps({
                "target_user": user_b_identity,
                "source_language": user_a_language,
                "target_language": user_b_language
            })
        )
    ]
)
```

### 3. Audio Routing Strategy

#### Option 1: Agent-Based Translation (Recommended)
- Each user gets their own dedicated translation agent
- Agent A listens to User B, translates to User A's language
- Agent B listens to User A, translates to User B's language
- Users don't hear agent voices directly - only the translations

#### Option 2: Direct Audio Processing
- Users publish audio to room
- Backend service processes audio streams
- Translated audio is published back to specific users

## Implementation Steps

1. **Fix Frontend Room Connection**
   - Create proper multi-user room component
   - Ensure both users can publish audio
   - Set up proper metadata for language identification

2. **Fix Backend Agent Logic**
   - Implement audio filtering to prevent feedback
   - Create per-user agent dispatch
   - Ensure agents only process audio from OTHER participants

3. **Test Audio Flow**
   - Verify User A's audio reaches User B's agent
   - Verify User B's audio reaches User A's agent
   - Verify translations are played to correct users

## Key LiveKit Concepts to Implement

1. **Track Filtering**: Agents must ignore their own audio output
2. **Metadata Usage**: Use participant metadata to identify languages
3. **Audio Routing**: Ensure translated audio goes to correct participant
4. **Permission Management**: Both users need `canPublish: true`

## Next Steps

1. Create new frontend component for translation rooms
2. Modify backend agent logic for proper audio filtering
3. Test with two real users in different languages
4. Implement audio quality optimizations
