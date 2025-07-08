import openai
import logging
from typing import Dict, List, Optional
from config import Config
from models import UserSession

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def get_system_prompt(self, session: UserSession) -> str:
        """Generate dynamic system prompt based on current session state"""
        
        base_prompt = """Sei un assistente vocale per un servizio clienti tecnico in Svizzera. 
        Parli sempre in italiano e sei cordiale, professionale e disponibile.
        
        IMPORTANTE: Le tue risposte devono essere BREVI e CHIARE perché saranno convertite in audio.
        Evita testi troppo lunghi, usa frasi semplici e dirette.
        """
        
        if session.current_step == "collecting_data":
            if not session.user_data.is_complete():
                missing = session.user_data.missing_fields()
                prompt = base_prompt + f"""
                FASE ATTUALE: Raccolta dati personali obbligatoria
                
                Devi raccogliere questi dati mancanti dell'utente:
                {', '.join(missing)}
                
                Chiedi UN SOLO dato alla volta in modo naturale e cordiale.
                Spiega che questi dati sono necessari per fornire assistenza personalizzata.
                
                Dati già raccolti: {session.user_data.dict(exclude_none=True)}
                """
            else:
                prompt = base_prompt + """
                FASE ATTUALE: Dati raccolti completamente
                
                Ora puoi offrire i servizi:
                1. Supporto tecnico per problemi comuni
                2. Prenotazione appuntamento
                
                Chiedi cosa preferisce fare l'utente.
                """
        
        elif session.current_step == "service_menu":
            prompt = base_prompt + """
            FASE ATTUALE: Menu servizi
            
            L'utente può scegliere tra:
            1. Supporto tecnico immediato
            2. Prenotare un appuntamento
            
            Fornisci assistenza tecnica per problemi comuni o guida verso la prenotazione.
            """
        
        elif session.current_step == "booking_appointment":
            prompt = base_prompt + """
            FASE ATTUALE: Prenotazione appuntamento
            
            Raccogli le informazioni per l'appuntamento:
            - Data preferita
            - Ora preferita  
            - Motivo dell'appuntamento
            
            Guida l'utente passo dopo passo.
            """
        
        return prompt
    
    async def get_response(self, user_message: str, session: UserSession) -> str:
        """Get AI response based on user message and session context"""
        try:
            # Build conversation history
            messages = [
                {"role": "system", "content": self.get_system_prompt(session)}
            ]
            
            # Add conversation history (last 10 messages to avoid token limits)
            for msg in session.conversation_history[-10:]:
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Get AI response
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=200,  # Keep responses short for voice
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Update conversation history
            session.conversation_history.append({"role": "user", "content": user_message})
            session.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error getting OpenAI response: {e}")
            return "Mi dispiace, ho avuto un problema tecnico. Puoi ripetere per favore?"
    
    def extract_user_data(self, user_message: str, current_data: Dict) -> Dict:
        """Extract and update user data from message using AI"""
        try:
            prompt = f"""
            Estrai i dati personali dal messaggio dell'utente e aggiornali.
            
            Dati attuali: {current_data}
            Messaggio utente: "{user_message}"
            
            Estrai solo i seguenti campi se presenti:
            - nome
            - cognome  
            - via_numero (via e numero civico)
            - paese_cap (paese e codice postale)
            - telefono
            - email
            
            Restituisci SOLO un JSON con i campi aggiornati.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.1
            )
            
            # Parse JSON response
            import json
            try:
                extracted_data = json.loads(response.choices[0].message.content)
                return extracted_data
            except json.JSONDecodeError:
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting user data: {e}")
            return {} 