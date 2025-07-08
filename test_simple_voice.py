#!/usr/bin/env python3
"""
Simple test for ElevenLabs API using environment variables directly
"""
import asyncio
import os
from elevenlabs import ElevenLabs

# Test environment variables (replace with actual values for testing)
ELEVENLABS_API_KEY = "sk_f2c1b3e4c45dd81b4e92b8ed3d8bb8f3be31cf9d"  # Replace with your actual key
VOICE_ID = "NKISxt4ff7agoGsJkaFY"

async def test_simple():
    print("🔍 Testing ElevenLabs API directly...")
    
    try:
        # Initialize client
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        print("✅ Client initialized")
        
        # Test connection by getting voices
        voices = client.voices.get_all()
        print(f"✅ Got {len(voices.voices)} voices")
        
        # Check if our voice exists
        voice_found = any(v.voice_id == VOICE_ID for v in voices.voices)
        print(f"Voice {VOICE_ID} found: {voice_found}")
        
        if not voice_found:
            print("Available voices:")
            for v in voices.voices[:5]:
                print(f"  - {v.name}: {v.voice_id}")
        
        # Test text to speech
        if voice_found:
            print("🎵 Testing TTS...")
            
            def generate_sync():
                return client.text_to_speech.convert(
                    voice_id=VOICE_ID,
                    text="Ciao! Questo è un test vocale.",
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
            
            audio_bytes = await asyncio.get_event_loop().run_in_executor(
                None, generate_sync
            )
            
            print(f"✅ Generated {len(audio_bytes)} bytes of audio")
            
            # Save test file
            with open("test_audio.mp3", "wb") as f:
                f.write(audio_bytes)
            print("✅ Saved to test_audio.mp3")
            
            return True
        else:
            print("❌ Cannot test TTS without valid voice ID")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple())
    if success:
        print("\n🎉 ElevenLabs is working!")
    else:
        print("\n💥 ElevenLabs test failed!") 