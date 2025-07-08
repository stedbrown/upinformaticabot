#!/usr/bin/env python3
"""
Test script to verify ElevenLabs API functionality
"""
import asyncio
import os
from config import Config
from services.elevenlabs_service import ElevenLabsService

async def test_elevenlabs():
    print("🔍 Testing ElevenLabs API...")
    
    # Check environment variables
    print(f"API Key set: {'Yes' if Config.ELEVENLABS_API_KEY else 'No'}")
    print(f"API Key length: {len(Config.ELEVENLABS_API_KEY) if Config.ELEVENLABS_API_KEY else 0}")
    print(f"Voice ID: {Config.VOICE_ID}")
    
    # Initialize service
    try:
        voice_service = ElevenLabsService()
        print("✅ ElevenLabs service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize ElevenLabs service: {e}")
        return False
    
    # Test connection
    try:
        connection_ok = voice_service.test_connection()
        if connection_ok:
            print("✅ ElevenLabs connection test passed")
        else:
            print("❌ ElevenLabs connection test failed")
            return False
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False
    
    # Test voice generation
    try:
        print("🎵 Testing voice generation...")
        test_text = "Ciao! Questo è un test vocale."
        
        file_path = await voice_service.generate_voice_response(test_text, 12345)
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ Voice file generated: {file_path}")
            print(f"📁 File size: {file_size} bytes")
            
            # Cleanup
            voice_service.cleanup_audio_file(file_path)
            print("🧹 Cleanup completed")
            return True
        else:
            print("❌ Voice generation failed - no file created")
            return False
            
    except Exception as e:
        print(f"❌ Voice generation error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_elevenlabs())
    if success:
        print("\n🎉 All tests passed! ElevenLabs is working correctly.")
    else:
        print("\n💥 Tests failed! Check the errors above.") 