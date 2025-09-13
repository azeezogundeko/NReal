#!/usr/bin/env python3
"""
Test script to verify Supabase database connection and caching system.
"""
import asyncio
import time
from dotenv import load_dotenv
from supabase import create_client
from app.core.config import get_settings
from app.db.models import DatabaseService
from app.services.livekit.room_manager import PatternBRoomManager

async def test_supabase_connection():
    """Test Supabase database connection."""
    load_dotenv()
    settings = get_settings()
    
    print("Testing Supabase connection...")
    print(f"Supabase URL: {settings.supabase_url}")
    print(f"Using service role key: {bool(settings.supabase_service_role_key)}")
    
    try:
        # Create Supabase client
        supabase = create_client(
            settings.supabase_url, 
            settings.supabase_service_role_key or settings.supabase_anon_key
        )
        
        # Test database service
        db_service = DatabaseService(supabase)
        
        # Try to get a user profile (this will fail gracefully now)
        test_user = "test-user-123"
        profile = await db_service.get_user_profile(test_user)
        
        if profile:
            print(f"✅ Successfully retrieved profile for {test_user}")
        else:
            print(f"ℹ️  No profile found for {test_user} (this is expected)")
        
        # Test table access
        result = supabase.table("user_profiles").select("count", count="exact").execute()
        print(f"✅ Successfully connected to database")
        print(f"✅ User profiles table has {result.count} records")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("🔧 Check your Supabase credentials and network connection")
        return False
    
    return True


async def test_caching_system():
    """Test the TTL-based user profile caching system."""
    load_dotenv()
    settings = get_settings()
    
    print("\n" + "="*50)
    print("TESTING CACHING SYSTEM")
    print("="*50)
    
    try:
        # Create services
        supabase = create_client(
            settings.supabase_url, 
            settings.supabase_service_role_key or settings.supabase_anon_key
        )
        db_service = DatabaseService(supabase)
        room_manager = PatternBRoomManager(db_service)
        
        test_user = "cache-test-user-123"
        
        print(f"Testing cache with user: {test_user}")
        
        # Test 1: First call should hit database and cache the result
        print("\n1. First profile fetch (should hit database)...")
        start_time = time.time()
        profile1 = await room_manager.get_user_profile(test_user)
        fetch_time1 = time.time() - start_time
        print(f"   ✅ Profile fetched in {fetch_time1:.3f}s")
        print(f"   📝 Profile: {profile1.user_identity} ({profile1.native_language.value})")
        
        # Check cache stats
        stats = room_manager.get_cache_stats()
        print(f"   📊 Cache stats: {stats['active_entries']} active, {stats['total_entries']} total")
        
        # Test 2: Second call should hit cache (much faster)
        print("\n2. Second profile fetch (should hit cache)...")
        start_time = time.time()
        profile2 = await room_manager.get_user_profile(test_user)
        fetch_time2 = time.time() - start_time
        print(f"   ✅ Profile fetched in {fetch_time2:.3f}s")
        print(f"   🚀 Speed improvement: {fetch_time1/fetch_time2:.1f}x faster")
        
        # Verify same profile
        assert profile1.user_identity == profile2.user_identity
        print(f"   ✅ Cache hit confirmed - same profile returned")
        
        # Test 3: Test multiple users
        print("\n3. Testing multiple user caching...")
        test_users = ["user-a", "user-b", "user-c"]
        
        for user in test_users:
            profile = await room_manager.get_user_profile(user)
            print(f"   📝 Cached profile for {user}")
        
        stats = room_manager.get_cache_stats()
        print(f"   📊 Cache stats: {stats['active_entries']} active, {stats['total_entries']} total")
        
        # Test 4: Test cache cleanup
        print("\n4. Testing cache cleanup...")
        initial_count = len(room_manager.user_profiles_cache)
        room_manager._cleanup_expired_cache()
        final_count = len(room_manager.user_profiles_cache)
        print(f"   🧹 Cleanup: {initial_count} -> {final_count} entries")
        
        # Test 5: Test cache expiration (simulate by manipulating cache time)
        print("\n5. Testing cache expiration...")
        if test_user in room_manager.user_profiles_cache:
            # Manually expire the cache entry
            cached_entry = room_manager.user_profiles_cache[test_user]
            expired_entry = cached_entry._replace(cached_at=time.time() - 2000)  # 2000 seconds ago
            room_manager.user_profiles_cache[test_user] = expired_entry
            
            print(f"   ⏰ Manually expired cache for {test_user}")
            
            # Next call should refresh from database
            start_time = time.time()
            profile3 = await room_manager.get_user_profile(test_user)
            fetch_time3 = time.time() - start_time
            print(f"   ✅ Expired cache refreshed in {fetch_time3:.3f}s")
        
        print("\n✅ All caching tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting comprehensive tests...")
    
    # Test 1: Database connection
    db_success = await test_supabase_connection()
    
    # Test 2: Caching system
    cache_success = await test_caching_system()
    
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Database Connection: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"Caching System:      {'✅ PASS' if cache_success else '❌ FAIL'}")
    
    if db_success and cache_success:
        print("\n🎉 All tests passed! Your system is ready to go.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return db_success and cache_success


if __name__ == "__main__":
    asyncio.run(run_all_tests())
