# Supabase Database Setup

This document explains how to set up and use Supabase as the database for the Translation Service.

## Prerequisites

1. **Supabase Account**: Create an account at [supabase.com](https://supabase.com)
2. **Supabase Project**: Create a new project in your Supabase dashboard
3. **Environment Variables**: Update your `.env` file with Supabase credentials

## Setup Steps

### 1. Environment Configuration

Add these variables to your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

You can find these values in your Supabase project dashboard under **Settings > API**.

### 2. Database Schema Setup

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `docs/SUPABASE_SETUP.sql`
4. Click **Run** to execute the SQL commands

This will create:
- `user_profiles` table for storing user language preferences
- `rooms` table for storing meeting room information
- `voice_avatars` table for storing available voice configurations
- Proper indexes for performance
- Row Level Security policies for data protection

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The Supabase client is already included in your `requirements.txt`:
```txt
supabase==2.3.0
psycopg2-binary==2.9.7
```

## Database Schema

### User Profiles Table

```sql
CREATE TABLE user_profiles (
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
```

### Rooms Table

```sql
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(255) UNIQUE NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    host_identity VARCHAR(255) NOT NULL,
    max_participants INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Voice Avatars Table

```sql
CREATE TABLE voice_avatars (
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
```

## Security Features

### Row Level Security (RLS)

The database uses Supabase's Row Level Security to ensure users can only access their own data:

- **User Profiles**: Users can only view/modify their own profiles
- **Rooms**: Users can view active rooms, but only hosts can modify their rooms
- **Voice Avatars**: Read-only access for all authenticated users

### Authentication

The system assumes you're using Supabase Auth for user authentication. The `user_identity` field should match the authenticated user's ID from Supabase Auth.

## Usage Examples

### Creating a User Profile

```python
from app.db.models import DatabaseService, UserProfile

# Assuming you have a Supabase client
db_service = DatabaseService(supabase_client)

profile = UserProfile(
    user_identity="user123",
    native_language="en",
    voice_avatar_id="21m00Tcm4TlvDq8ikWAM",
    voice_provider="elevenlabs",
    formal_tone=False,
    preserve_emotion=True
)

await db_service.create_user_profile(profile)
```

### Querying User Profiles

```python
# Get a specific user's profile
profile = await db_service.get_user_profile("user123")

# Update user preferences
await db_service.update_user_profile("user123", {
    "formal_tone": True,
    "preserve_emotion": False
})
```

### Managing Rooms

```python
# Create a new room
room = Room(
    room_id="room-abc-123",
    room_name="Team Meeting",
    host_identity="user123",
    max_participants=10
)

await db_service.create_room(room)

# List active rooms
rooms = await db_service.list_active_rooms()

# Deactivate a room
await db_service.deactivate_room("room-abc-123")
```

## Performance Considerations

### Indexes

The following indexes are created for optimal performance:

```sql
CREATE INDEX idx_user_profiles_identity ON user_profiles(user_identity);
CREATE INDEX idx_rooms_room_id ON rooms(room_id);
CREATE INDEX idx_rooms_active ON rooms(is_active);
CREATE INDEX idx_voice_avatars_language ON voice_avatars(language);
```

### Caching Strategy

The application uses a caching layer to reduce database queries:

- **User profiles** are cached in memory after first access
- **Voice avatars** are relatively static and can be cached
- **Room queries** are optimized with proper indexing

## Monitoring & Maintenance

### Database Monitoring

Use Supabase's built-in monitoring tools to track:

- Query performance
- Database size and usage
- Connection counts
- Error rates

### Backup Strategy

Supabase provides automatic backups, but you should also:

1. Regularly export important data
2. Test backup restoration procedures
3. Monitor database health metrics

### Scaling Considerations

As your application grows:

1. **Connection Pooling**: Use connection pooling for better performance
2. **Read Replicas**: Consider read replicas for heavy read workloads
3. **Caching Layer**: Implement Redis for frequently accessed data
4. **Database Sharding**: Shard by region if needed for global deployments

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check your Supabase URL and API keys
2. **Permission Errors**: Verify RLS policies are correctly configured
3. **Performance Issues**: Check query execution plans and add missing indexes

### Debugging

Enable detailed logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support

For Supabase-specific issues:
- Check the [Supabase Documentation](https://supabase.com/docs)
- Use the [Supabase Community Forum](https://supabase.com/community)
- Check [Supabase Status](https://status.supabase.com) for service issues

## Migration from In-Memory Storage

If you're migrating from the previous in-memory storage:

1. **Backup existing data** (if any)
2. **Run the SQL setup** script
3. **Update your environment variables**
4. **Test the application** with database connectivity
5. **Gradually migrate** any existing user data

The new database layer is designed to be backward compatible with minimal code changes.
