import logging
import aiofiles
from elevenlabs import Voice, VoiceSettings, generate, set_api_key
from config import Config
from typing import Optional
import os

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        set_api_key(Config.ELEVENLABS_API_KEY)
        self.voice_id = Config.VOICE_ID
        
    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs API"""
        try:
            # Generate audio with specified voice
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=self.voice_id,
                    settings=VoiceSettings(
                        stability=0.71,
                        similarity_boost=0.5,
                        style=0.0,
                        use_speaker_boost=True
                    )
                ),
                model="eleven_multilingual_v2"  # Supports Italian
            )
            
            logger.info(f"Generated audio for text: {text[:50]}...")
            return audio
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return None
    
    async def save_audio_file(self, audio_data: bytes, filename: str) -> str:
        """Save audio data to file and return file path"""
        try:
            # Create temp directory if it doesn't exist
            os.makedirs("temp", exist_ok=True)
            
            file_path = f"temp/{filename}"
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(audio_data)
            
            logger.info(f"Audio saved to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            raise
    
    async def generate_voice_response(self, text: str, user_id: int) -> Optional[str]:
        """Generate voice response and return file path"""
        try:
            # Generate audio
            audio_data = await self.text_to_speech(text)
            if not audio_data:
                return None
            
            # Save to file
            filename = f"response_{user_id}_{hash(text)}.mp3"
            file_path = await self.save_audio_file(audio_data, filename)
            
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