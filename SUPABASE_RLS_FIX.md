# Fix for Supabase RLS Policy Error

The error you're encountering is due to Row Level Security (RLS) policies in Supabase that prevent unauthorized database operations.

## Problem
```
"detail": "{'message': 'new row violates row-level security policy for table \"rooms\"', 'code': '42501', 'hint': None, 'details': None}"
```

## Root Cause
Your backend is using the `SUPABASE_ANON_KEY` instead of the `SUPABASE_SERVICE_ROLE_KEY`. The anon key is subject to RLS policies, while the service role key bypasses them for backend operations.

## Solution

### Step 1: Update Environment Variables
Make sure your backend `.env` file has both keys:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

You can find these keys in your Supabase dashboard under **Settings > API**.

### Step 2: Backend Code Fix (Already Applied)
I've updated `backend/app/main.py` to use the service role key:

```python
# Initialize Supabase client with service role key for backend operations
# Service role key bypasses RLS policies for server-side operations
supabase_key = settings.supabase_service_role_key or settings.supabase_anon_key
supabase = create_client(settings.supabase_url, supabase_key)
```

### Step 3: Alternative Quick Fix (If Service Key Not Available)
If you don't have the service role key set up, you can temporarily disable RLS for the rooms table by running this SQL in your Supabase SQL Editor:

```sql
-- Temporary fix: Disable RLS for rooms table
ALTER TABLE rooms DISABLE ROW LEVEL SECURITY;
```

**⚠️ Warning**: This makes the rooms table accessible to anyone with database access. Use only for development.

### Step 4: Restart Your Backend
After updating the environment variables, restart your backend server:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

## Verification
Test the room creation by:
1. Starting your backend server
2. Opening the frontend
3. Creating a new room
4. Check that no RLS errors occur

## Security Notes
- **Service Role Key**: Bypasses all RLS policies - use only in backend code, never expose to frontend
- **Anon Key**: Subject to RLS policies - safe to use in frontend applications
- Keep your service role key secure and never commit it to version control

## Additional RLS Policies
If you want to keep RLS enabled but make it more permissive for development, you can run:

```sql
-- More permissive room policies (alternative to disabling RLS)
DROP POLICY IF EXISTS "Users can create rooms" ON rooms;
CREATE POLICY "Anyone can create rooms" ON rooms FOR INSERT WITH CHECK (true);
```
