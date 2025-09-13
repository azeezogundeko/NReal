# Multi-User Agent Coordination System

## Overview

The LiveKit translation system now supports coordinated multi-user scenarios where multiple agents work together in the same room to provide efficient real-time translation for all participants.

## Architecture Changes

### Before (Independent Agents)
```
Room: "meeting-123"
├── User A (English) → Agent A (processes all participants independently)
├── User B (Spanish) → Agent B (processes all participants independently)
└── User C (French)  → No agent
```

**Problems:**
- Duplicate processing: Both Agent A and Agent B translate the same speech
- Resource waste: Multiple agents doing the same translation work
- No coordination: Agents don't know about each other

### After (Coordinated Agents)
```
Room: "meeting-123"
├── User A (English) → Agent A ┐
├── User B (Spanish) → Agent B ├─→ Coordinated Translation Service
└── User C (French)  → No agent ┘
```

**Benefits:**
- Efficient processing: Each translation is done once and distributed
- Resource optimization: Parallel translation for different target languages
- Agent awareness: Agents know about and coordinate with each other

## Implementation Details

### 1. Room-Level Agent Registry

```python
class LiveKitService:
    def __init__(self, room_manager):
        # Room-level agent registry: room_name -> {user_identity -> agent}
        self.room_agents: Dict[str, Dict[str, UserTranslationAgent]] = {}
```

### 2. Agent Coordination on Join

When a user joins a room:

```python
async def create_user_agent(self, user_identity: str, ctx: JobContext):
    # 1. Create agent with service reference
    agent = UserTranslationAgent(profile, livekit_service=self)
    
    # 2. Register in room registry
    room_name = ctx.room.name
    self.room_agents[room_name][user_identity] = agent
    
    # 3. Notify existing agents
    await self._notify_agents_of_new_agent(room_name, agent)
```

### 3. Coordinated Translation Process

When someone speaks in the room:

```python
async def coordinate_translation_task(self, room_name: str, participant_identity: str, 
                                    speech_text: str, source_language: SupportedLanguage):
    """Coordinate translation among all agents in the room"""
    
    # 1. Identify which agents need translation
    translation_tasks = []
    for user_identity, agent in self.room_agents[room_name].items():
        if (user_identity != participant_identity and 
            agent.user_profile.native_language != source_language):
            
            # 2. Create translation task for each agent
            task = agent.translate_for_user(speech_text, source_language, participant_identity)
            translation_tasks.append((user_identity, task))
    
    # 3. Execute all translations in parallel
    results = await asyncio.gather(*[task for _, task in translation_tasks])
    
    # 4. Return translations mapped to users
    return {user_id: result for (user_id, _), result in zip(translation_tasks, results)}
```

### 4. Agent-to-Agent Communication

```python
class UserTranslationAgent:
    def __init__(self, user_profile, livekit_service=None):
        self.livekit_service = livekit_service
        self.connected_agents: Dict[str, 'UserTranslationAgent'] = {}
    
    async def on_agent_joined(self, other_agent):
        """Handle when another agent joins the same room"""
        self.connected_agents[other_agent.user_profile.user_identity] = other_agent
        logging.info(f"Agent {self.user_profile.user_identity} connected to {other_agent.user_profile.user_identity}")
```

## Usage Example: 2-User Scenario

### Scenario Setup
- **User A**: English speaker joins room "meeting-123"
- **User B**: Spanish speaker joins room "meeting-123"

### Step-by-Step Flow

1. **User A Joins**
   ```python
   # Agent A is created and registered
   room_agents["meeting-123"] = {"userA": AgentA}
   ```

2. **User B Joins**
   ```python
   # Agent B is created and registered
   room_agents["meeting-123"] = {"userA": AgentA, "userB": AgentB}
   
   # Agents are notified of each other
   await AgentA.on_agent_joined(AgentB)
   await AgentB.on_agent_joined(AgentA)
   ```

3. **User A Speaks (in English)**
   ```python
   # Speech detected: "Hello, how are you?"
   
   # Coordinated translation:
   translations = await coordinate_translation_task(
       "meeting-123", 
       "userA", 
       "Hello, how are you?", 
       SupportedLanguage.ENGLISH
   )
   
   # Result: {"userB": "Hola, ¿cómo estás?"}
   # Agent B plays Spanish translation to User B
   ```

4. **User B Speaks (in Spanish)**
   ```python
   # Speech detected: "Muy bien, gracias"
   
   # Coordinated translation:
   translations = await coordinate_translation_task(
       "meeting-123", 
       "userB", 
       "Muy bien, gracias", 
       SupportedLanguage.SPANISH
   )
   
   # Result: {"userA": "Very well, thank you"}
   # Agent A plays English translation to User A
   ```

## Benefits of the New System

### 1. **Efficiency**
- Each translation is computed once, not per agent
- Parallel processing for multiple target languages
- Reduced computational overhead

### 2. **Scalability**
- System scales better with more users
- O(n) translation complexity instead of O(n²)
- Shared resource utilization

### 3. **Coordination**
- Agents are aware of each other
- Can implement advanced features like speaker identification
- Better error handling and fallback mechanisms

### 4. **Resource Management**
- Centralized translation coordination
- Better memory and CPU utilization
- Easier monitoring and debugging

## Backward Compatibility

The system maintains backward compatibility:
- If `livekit_service` is not provided, agents work independently (original behavior)
- Existing single-user scenarios continue to work without changes
- Gradual migration path for existing deployments

## Testing the System

To test the multi-user coordination:

1. Create two user profiles with different languages
2. Join both users to the same room
3. Verify agents are created and registered
4. Test speech from each user
5. Confirm translations are coordinated and delivered correctly

The system logs will show coordination messages:
```
Agent userA connected to agent userB
Speech detected from userA: Hello, how are you?...
Received coordinated translation: Hola, ¿cómo estás?...
```
