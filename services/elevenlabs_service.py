import logging
import aiofiles
import asyncio
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from config import Config
from typing import Optional
import os

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
        self.voice_id = Config.VOICE_ID
        logger.info(f"ElevenLabs service initialized with voice ID: {self.voice_id}")
        
    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs API"""
        try:
            logger.info(f"Generating speech for text: {text[:100]}...")
            
            # Run the sync generate method in a thread pool
            def generate_sync():
                return self.client.generate(
                    text=text,
                    voice=self.voice_id,
                    voice_settings=VoiceSettings(
                        stability=0.71,
                        similarity_boost=0.5,
                        style=0.0,
                        use_speaker_boost=True
                    ),
                    model="eleven_multilingual_v2"  # Supports Italian
                )
            
            # Convert generator to bytes
            audio_generator = await asyncio.get_event_loop().run_in_executor(
                None, generate_sync
            )
            
            # Collect all audio chunks
            audio_data = b""
            for chunk in audio_generator:
                if chunk:
                    audio_data += chunk
            
            logger.info(f"Generated audio data size: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            logger.error(f"Voice ID used: {self.voice_id}")
            logger.error(f"Text length: {len(text)} characters")
            return None
    
    async def save_audio_file(self, audio_data: bytes, filename: str) -> str:
        """Save audio data to file and return file path"""
        try:
            # Create temp directory if it doesn't exist
            os.makedirs("temp", exist_ok=True)
            
            file_path = f"temp/{filename}"
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(audio_data)
            
            logger.info(f"Audio saved to: {file_path} ({len(audio_data)} bytes)")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            raise
    
    async def generate_voice_response(self, text: str, user_id: int) -> Optional[str]:
        """Generate voice response and return file path"""
        try:
            logger.info(f"Starting voice generation for user {user_id}")
            
            # Check if text is too long
            if len(text) > 5000:
                text = text[:4900] + "..."
                logger.warning("Text truncated to fit ElevenLabs limits")
            
            # Generate audio
            audio_data = await self.text_to_speech(text)
            if not audio_data:
                logger.error("No audio data generated")
                return None
            
            # Save to file
            filename = f"response_{user_id}_{hash(text) % 100000}.mp3"
            file_path = await self.save_audio_file(audio_data, filename)
            
            logger.info(f"Voice response generated successfully: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating voice response: {e}")
            return None
    
    def cleanup_audio_file(self, file_path: str):
        """Clean up temporary audio file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up audio file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up audio file: {e}")
    
    def test_connection(self) -> bool:
        """Test ElevenLabs API connection"""
        try:
            # Try to get available voices to test connection
            voices = self.client.voices.get_all()
            logger.info(f"ElevenLabs connection test successful. Found {len(voices.voices)} voices")
            
            # Check if our voice ID exists
            voice_found = any(v.voice_id == self.voice_id for v in voices.voices)
            if voice_found:
                logger.info(f"Voice ID {self.voice_id} found in available voices")
            else:
                logger.warning(f"Voice ID {self.voice_id} not found in available voices")
                # List available voice IDs for debugging
                available_voices = [f"{v.name}: {v.voice_id}" for v in voices.voices[:5]]
                logger.info(f"Available voices: {available_voices}")
            
            return voice_found
            
        except Exception as e:
            logger.error(f"ElevenLabs connection test failed: {e}")
            return False 