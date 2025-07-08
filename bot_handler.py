import logging
import re
from typing import Dict, Optional
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from models import UserSession, UserData, AppointmentRequest
from services import OpenAIService, ElevenLabsService, CalendarService
from config import SWISS_PHONE_PATTERN, EMAIL_PATTERN

logger = logging.getLogger(__name__)

class TelegramBotHandler:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.voice_service = ElevenLabsService()
        self.calendar_service = CalendarService()
        self.user_sessions: Dict[int, UserSession] = {}
        
        # Test ElevenLabs connection
        try:
            voice_working = self.voice_service.test_connection()
            if voice_working:
                logger.info("ElevenLabs service is working correctly")
            else:
                logger.warning("ElevenLabs service connection test failed - voice responses may not work")
        except Exception as e:
            logger.error(f"Error testing ElevenLabs connection: {e}")
    
    def get_or_create_session(self, user_id: int, chat_id: int) -> UserSession:
        """Get existing user session or create new one"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(
                user_id=user_id,
                chat_id=chat_id
            )
        return self.user_sessions[user_id]
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main message handler"""
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            user_message = update.message.text
            
            # Get or create user session
            session = self.get_or_create_session(user_id, chat_id)
            
            logger.info(f"Received message from user {user_id}: {user_message}")
            
            # Process message based on current step
            if session.current_step == "collecting_data":
                await self._handle_data_collection(update, context, session, user_message)
            elif session.current_step == "service_menu":
                await self._handle_service_menu(update, context, session, user_message)
            elif session.current_step == "booking_appointment":
                await self._handle_appointment_booking(update, context, session, user_message)
            else:
                # Default to data collection
                session.current_step = "collecting_data"
                await self._handle_data_collection(update, context, session, user_message)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_voice_response(
                update, 
                "Mi dispiace, c'è stato un errore. Puoi riprovare per favore?"
            )
    
    async def _handle_data_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                    session: UserSession, user_message: str):
        """Handle user data collection phase"""
        try:
            # Extract data from user message using AI
            extracted_data = self.openai_service.extract_user_data(
                user_message, 
                session.user_data.dict(exclude_none=True)
            )
            
            # Update user data with extracted information
            for field, value in extracted_data.items():
                if hasattr(session.user_data, field) and value:
                    try:
                        setattr(session.user_data, field, value)
                    except ValueError as e:
                        # Validation error - inform user
                        await self._send_voice_response(update, str(e))
                        return
            
            # Check if data collection is complete
            if session.user_data.is_complete():
                session.current_step = "service_menu"
                response = await self.openai_service.get_response(user_message, session)
            else:
                # Continue collecting missing data
                response = await self.openai_service.get_response(user_message, session)
            
            await self._send_voice_response(update, response)
            
        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            await self._send_voice_response(
                update, 
                "Mi dispiace, non ho capito bene. Puoi ripetere i tuoi dati?"
            )
    
    async def _handle_service_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 session: UserSession, user_message: str):
        """Handle service menu interactions"""
        try:
            # Check if user wants to book appointment
            if any(keyword in user_message.lower() for keyword in 
                   ['appuntamento', 'prenota', 'prenotazione', 'calendario']):
                session.current_step = "booking_appointment"
                session.appointment_request = AppointmentRequest(user_data=session.user_data)
            
            # Get AI response
            response = await self.openai_service.get_response(user_message, session)
            await self._send_voice_response(update, response)
            
        except Exception as e:
            logger.error(f"Error in service menu: {e}")
            await self._send_voice_response(
                update, 
                "Cosa posso fare per te? Supporto tecnico o prenotazione appuntamento?"
            )
    
    async def _handle_appointment_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        session: UserSession, user_message: str):
        """Handle appointment booking process"""
        try:
            appointment_req = session.appointment_request
            
            # Extract appointment information using AI
            response = await self.openai_service.get_response(user_message, session)
            
            # Check for date information
            if not appointment_req.data_preferita:
                date_match = self._extract_date(user_message)
                if date_match:
                    appointment_req.data_preferita = date_match
            
            # Check for time information
            if not appointment_req.ora_preferita:
                time_match = self._extract_time(user_message)
                if time_match:
                    appointment_req.ora_preferita = time_match
            
            # Check for reason
            if not appointment_req.motivo and len(user_message.split()) > 2:
                appointment_req.motivo = user_message
            
            # If all appointment data is collected, try to book
            if appointment_req.is_complete():
                success = await self._book_appointment(appointment_req)
                if success:
                    response = "Perfetto! Il tuo appuntamento è stato confermato. Riceverai una email di conferma a breve."
                    session.current_step = "service_menu"  # Return to service menu
                else:
                    response = "Mi dispiace, non sono riuscito a prenotare l'appuntamento. Vuoi provare con un'altra data o ora?"
            
            await self._send_voice_response(update, response)
            
        except Exception as e:
            logger.error(f"Error in appointment booking: {e}")
            await self._send_voice_response(
                update, 
                "C'è stato un problema con la prenotazione. Puoi riprovare?"
            )
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text message"""
        # Simple date extraction patterns
        patterns = [
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    try:
                        # Try different date formats
                        if int(groups[0]) > 31:  # Likely YYYY-MM-DD
                            date = datetime.strptime(f"{groups[0]}-{groups[1]}-{groups[2]}", "%Y-%m-%d")
                        else:  # Likely DD/MM/YYYY
                            date = datetime.strptime(f"{groups[2]}-{groups[1]}-{groups[0]}", "%Y-%m-%d")
                        return date.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
        
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from text message"""
        # Time extraction patterns
        patterns = [
            r'(\d{1,2}):(\d{2})',  # HH:MM
            r'(\d{1,2})\s*(am|pm)',  # H AM/PM
            r'alle\s*(\d{1,2})',  # "alle 14"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                if len(match.groups()) >= 2 and match.group(2).isdigit():
                    # HH:MM format
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
                else:
                    # Hour only
                    hour = int(match.group(1))
                    if 0 <= hour <= 23:
                        return f"{hour:02d}:00"
        
        return None
    
    async def _book_appointment(self, appointment_request: AppointmentRequest) -> bool:
        """Book the appointment in Google Calendar"""
        try:
            # Check availability first
            is_available = await self.calendar_service.check_availability(
                appointment_request.data_preferita,
                appointment_request.ora_preferita
            )
            
            if not is_available:
                return False
            
            # Create appointment
            event_link = await self.calendar_service.create_appointment(appointment_request)
            return event_link is not None
            
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return False
    
    async def _send_voice_response(self, update: Update, text: str):
        """Send voice response to user"""
        try:
            user_id = update.effective_user.id
            logger.info(f"Attempting to send voice response to user {user_id}")
            
            # Generate voice response
            voice_file_path = await self.voice_service.generate_voice_response(text, user_id)
            
            if voice_file_path:
                logger.info(f"Voice file generated: {voice_file_path}")
                # Send voice message
                with open(voice_file_path, 'rb') as audio_file:
                    await update.message.reply_voice(
                        voice=audio_file,
                        caption="🎵 Risposta vocale"
                    )
                
                # Clean up temporary file
                self.voice_service.cleanup_audio_file(voice_file_path)
                logger.info("Voice response sent successfully")
            else:
                logger.warning("Voice generation failed, sending text fallback")
                # Check if it's an API key issue
                if not hasattr(self.voice_service, 'api_key_valid') or not self.voice_service.api_key_valid:
                    fallback_message = f"🔊 {text}\n\n⚠️ Servizio vocale temporaneamente non disponibile (problema configurazione)"
                else:
                    fallback_message = f"🔊 {text}\n\n⚠️ Servizio vocale temporaneamente non disponibile"
                
                # Fallback to text message if voice generation fails
                await update.message.reply_text(fallback_message)
                
        except Exception as e:
            logger.error(f"Error sending voice response: {e}")
            # Fallback to text
            try:
                await update.message.reply_text(f"🔊 {text}\n\n⚠️ Errore nel servizio vocale")
            except Exception as fallback_error:
                logger.error(f"Even text fallback failed: {fallback_error}")
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Reset or create new session
        self.user_sessions[user_id] = UserSession(
            user_id=user_id,
            chat_id=chat_id,
            current_step="collecting_data"
        )
        
        welcome_message = """Ciao! Sono l'assistente vocale del servizio clienti.

Per poterti aiutare al meglio, ho bisogno di raccogliere alcune informazioni personali. 

Iniziamo: come ti chiami?"""
        
        await self._send_voice_response(update, welcome_message)
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """Sono qui per aiutarti con:

🔧 Supporto tecnico per problemi comuni
📅 Prenotazione appuntamenti

Parlami dei tuoi problemi o dimmi se vuoi prenotare un appuntamento!"""
        
        await self._send_voice_response(update, help_message) 