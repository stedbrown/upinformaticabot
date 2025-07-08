import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Configuration
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    VOICE_ID = os.getenv('VOICE_ID')
    
    # Google Calendar Configuration
    GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
    CALENDAR_ID = os.getenv('CALENDAR_ID')
    
    # Validate required environment variables
    @classmethod
    def validate(cls):
        required_vars = [
            'TELEGRAM_TOKEN',
            'OPENAI_API_KEY', 
            'ELEVENLABS_API_KEY',
            'VOICE_ID',
            'GOOGLE_CREDENTIALS_JSON',
            'CALENDAR_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate Google credentials JSON
        try:
            json.loads(cls.GOOGLE_CREDENTIALS_JSON)
        except json.JSONDecodeError:
            raise ValueError("GOOGLE_CREDENTIALS_JSON is not valid JSON")
        
        return True

# Swiss phone number validation pattern
SWISS_PHONE_PATTERN = r'^(\+41|0041|0)[1-9][0-9]{8}$'

# Email validation pattern  
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$' 