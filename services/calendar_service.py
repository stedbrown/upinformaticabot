import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import Config
from models import UserData, AppointmentRequest

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self):
        self.calendar_id = Config.CALENDAR_ID
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar using service account"""
        try:
            # Parse credentials from environment variable
            creds_info = json.loads(Config.GOOGLE_CREDENTIALS_JSON)
            
            # Create credentials object
            credentials = service_account.Credentials.from_service_account_info(
                creds_info,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            # Build service
            service = build('calendar', 'v3', credentials=credentials)
            logger.info("Successfully authenticated with Google Calendar")
            return service
            
        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar: {e}")
            raise
    
    async def check_availability(self, date_str: str, time_str: str, duration_minutes: int = 60) -> bool:
        """Check if a time slot is available"""
        try:
            # Parse date and time
            appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # Create time range for the appointment
            start_time = appointment_datetime.isoformat() + 'Z'
            end_time = (appointment_datetime + timedelta(minutes=duration_minutes)).isoformat() + 'Z'
            
            # Query calendar for events in this time range
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # If no events found, slot is available
            is_available = len(events) == 0
            logger.info(f"Availability check for {date_str} {time_str}: {'Available' if is_available else 'Busy'}")
            
            return is_available
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False
    
    async def create_appointment(self, appointment_request: AppointmentRequest) -> Optional[str]:
        """Create a new appointment in Google Calendar"""
        try:
            user_data = appointment_request.user_data
            
            # Parse appointment datetime
            appointment_datetime = datetime.strptime(
                f"{appointment_request.data_preferita} {appointment_request.ora_preferita}", 
                "%Y-%m-%d %H:%M"
            )
            
            # Create event
            event = {
                'summary': f'Appuntamento - {user_data.nome} {user_data.cognome}',
                'description': f"""
                Motivo: {appointment_request.motivo}
                
                Dettagli cliente:
                Nome: {user_data.nome} {user_data.cognome}
                Telefono: {user_data.telefono}
                Email: {user_data.email}
                Indirizzo: {user_data.via_numero}, {user_data.paese_cap}
                
                Prenotato tramite bot Telegram
                """.strip(),
                'start': {
                    'dateTime': appointment_datetime.isoformat(),
                    'timeZone': 'Europe/Zurich',
                },
                'end': {
                    'dateTime': (appointment_datetime + timedelta(hours=1)).isoformat(),
                    'timeZone': 'Europe/Zurich',
                },
                'attendees': [
                    {'email': user_data.email, 'displayName': f'{user_data.nome} {user_data.cognome}'},
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 60},  # 1 hour before
                    ],
                },
            }
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            event_id = created_event['id']
            event_link = created_event.get('htmlLink', '')
            
            logger.info(f"Created appointment with ID: {event_id}")
            return event_link
            
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return None
    
    async def get_available_slots(self, date_str: str, start_hour: int = 9, end_hour: int = 17) -> List[str]:
        """Get available time slots for a given date"""
        try:
            available_slots = []
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Check each hour slot
            for hour in range(start_hour, end_hour):
                time_str = f"{hour:02d}:00"
                if await self.check_availability(date_str, time_str):
                    available_slots.append(time_str)
            
            logger.info(f"Found {len(available_slots)} available slots for {date_str}")
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []
    
    async def cancel_appointment(self, event_id: str) -> bool:
        """Cancel an appointment"""
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Cancelled appointment with ID: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            return False 