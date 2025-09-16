-- Fix for Room RLS Policy Issue
-- Run this in your Supabase SQL Editor

-- Option 1: Disable RLS for rooms table (if not using Supabase Auth)
ALTER TABLE rooms DISABLE ROW LEVEL SECURITY;

-- Option 2: Alternative - Create more permissive policies for rooms
-- (Uncomment the lines below if you prefer to keep RLS enabled but make it more permissive)

-- DROP POLICY IF EXISTS "Users can create rooms" ON rooms;
-- DROP POLICY IF EXISTS "Room hosts can update their rooms" ON rooms;

-- -- Allow any authenticated user to create rooms
-- CREATE POLICY "Anyone can create rooms" ON rooms
--     FOR INSERT WITH CHECK (true);

-- -- Allow room hosts to update their rooms (based on host_identity field)
-- CREATE POLICY "Room hosts can update their rooms" ON rooms
--     FOR UPDATE USING (host_identity = host_identity);

-- Option 3: Use service role for backend operations
-- (This would require updating your backend to use the service role key)
-- No SQL changes needed, but you'd need to update your Supabase client configuration
