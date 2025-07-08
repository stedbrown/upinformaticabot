from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime
import re
from config import SWISS_PHONE_PATTERN, EMAIL_PATTERN

class UserData(BaseModel):
    """Model for collecting and validating user personal data"""
    nome: Optional[str] = None
    cognome: Optional[str] = None
    via_numero: Optional[str] = None
    paese_cap: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    
    @validator('telefono')
    def validate_phone(cls, v):
        if v and not re.match(SWISS_PHONE_PATTERN, v):
            raise ValueError('Numero di telefono svizzero non valido. Formato: +41XXXXXXXXX o 0XXXXXXXXX')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(EMAIL_PATTERN, v):
            raise ValueError('Indirizzo email non valido')
        return v
    
    def is_complete(self) -> bool:
        """Check if all required fields are filled"""
        required_fields = ['nome', 'cognome', 'via_numero', 'paese_cap', 'telefono', 'email']
        return all(getattr(self, field) is not None for field in required_fields)
    
    def missing_fields(self) -> list:
        """Return list of missing required fields"""
        required_fields = ['nome', 'cognome', 'via_numero', 'paese_cap', 'telefono', 'email']
        return [field for field in required_fields if getattr(self, field) is None]

class AppointmentRequest(BaseModel):
    """Model for appointment booking requests"""
    user_data: UserData
    data_preferita: Optional[str] = None
    ora_preferita: Optional[str] = None
    motivo: Optional[str] = None
    
    def is_complete(self) -> bool:
        """Check if appointment request is complete"""
        return (self.user_data.is_complete() and 
                self.data_preferita and 
                self.ora_preferita and 
                self.motivo)

class UserSession(BaseModel):
    """Model for tracking user session state"""
    user_id: int
    chat_id: int
    user_data: UserData = UserData()
    appointment_request: Optional[AppointmentRequest] = None
    current_step: str = "collecting_data"  # collecting_data, service_menu, booking_appointment
    conversation_history: list = []
    
    class Config:
        arbitrary_types_allowed = True 