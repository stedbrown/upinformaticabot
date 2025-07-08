# Telegram Voice Bot per Servizio Clienti

Bot Telegram vocale che estende il servizio clienti, raccoglie dati utente, fornisce supporto tecnico e gestisce prenotazioni automatiche su Google Calendar.

## 🚀 Caratteristiche

- **Risposte vocali**: Tutte le risposte sono generate con ElevenLabs
- **Raccolta dati obbligatoria**: Raccoglie nome, cognome, indirizzo, telefono ed email prima di fornire servizi
- **Supporto tecnico**: Assistenza AI per problemi comuni
- **Prenotazioni automatiche**: Integrazione con Google Calendar
- **Validazione dati**: Validazione numero svizzero ed email
- **Deploy su Railway**: Configurazione pronta per il deploy

## 📋 Prerequisiti

1. **Token Telegram Bot**: Ottieni da [@BotFather](https://t.me/botfather)
2. **API Key OpenAI**: Da [platform.openai.com](https://platform.openai.com)
3. **API Key ElevenLabs**: Da [elevenlabs.io](https://elevenlabs.io)
4. **Google Service Account**: Per accesso a Google Calendar
5. **Account Railway**: Per il deploy

## 🛠️ Installazione Locale

1. **Clona il repository**
```bash
git clone <your-repo-url>
cd upinfobot
```

2. **Installa le dipendenze**
```bash
pip install -r requirements.txt
```

3. **Configura le variabili d'ambiente**
Crea un file `.env` nella root del progetto:

```env
TELEGRAM_TOKEN=7984832281:AAFsly4R9q2pEy6EMuMlO5QmG1dYybqlhw0
OPENAI_API_KEY=sk-proj-your-openai-key-here
ELEVENLABS_API_KEY=sk_9f5-your-elevenlabs-key-here
VOICE_ID=NKISxt4ff7agoGsJkaFY
GOOGLE_CREDENTIALS_JSON={"type": "service_account", "project_id": "..."}
CALENDAR_ID=stefano.vananti@gmail.com
```

4. **Avvia il bot**
```bash
python main.py
```

## ☁️ Deploy su Railway

### Metodo 1: Deploy Automatico

1. Fai fork di questo repository
2. Vai su [railway.app](https://railway.app)
3. Clicca "New Project" → "Deploy from GitHub repo"
4. Seleziona il tuo fork
5. Aggiungi le variabili d'ambiente nel dashboard Railway

### Metodo 2: Deploy CLI

1. **Installa Railway CLI**
```bash
npm install -g @railway/cli
```

2. **Login e deploy**
```bash
railway login
railway init
railway up
```

3. **Configura le variabili d'ambiente**
```bash
railway variables set TELEGRAM_TOKEN=your_token
railway variables set OPENAI_API_KEY=your_key
railway variables set ELEVENLABS_API_KEY=your_key
railway variables set VOICE_ID=your_voice_id
railway variables set GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
railway variables set CALENDAR_ID=your_calendar_id
```

## 🔧 Configurazione Google Calendar

1. **Crea un progetto Google Cloud**
   - Vai su [console.cloud.google.com](https://console.cloud.google.com)
   - Crea un nuovo progetto

2. **Abilita Google Calendar API**
   - Vai su "APIs & Services" → "Library"
   - Cerca "Google Calendar API" e abilitala

3. **Crea Service Account**
   - Vai su "APIs & Services" → "Credentials"
   - Clicca "Create Credentials" → "Service Account"
   - Scarica la chiave JSON

4. **Condividi il calendario**
   - Apri Google Calendar
   - Impostazioni calendario → Condividi con persone specifiche
   - Aggiungi l'email del service account con permessi "Apportare modifiche agli eventi"

5. **Copia il JSON come variabile d'ambiente**
   - Il contenuto del file JSON va in `GOOGLE_CREDENTIALS_JSON`

## 🎯 Utilizzo

### Comandi Bot

- `/start` - Avvia conversazione e raccolta dati
- `/help` - Mostra aiuto

### Flusso Conversazione

1. **Raccolta Dati** (obbligatoria)
   - Nome e cognome
   - Via e numero civico
   - Paese e CAP
   - Telefono svizzero
   - Email

2. **Menu Servizi**
   - Supporto tecnico
   - Prenotazione appuntamento

3. **Prenotazione Appuntamento**
   - Data preferita
   - Ora preferita
   - Motivo appuntamento
   - Conferma automatica

## 📁 Struttura Progetto

```
upinfobot/
├── main.py                 # Entry point applicazione
├── config.py              # Configurazione e variabili d'ambiente
├── models.py              # Modelli dati Pydantic
├── bot_handler.py         # Gestione logica bot Telegram
├── services/
│   ├── __init__.py
│   ├── openai_service.py  # Integrazione OpenAI GPT
│   ├── elevenlabs_service.py  # Text-to-speech
│   └── calendar_service.py    # Google Calendar
├── requirements.txt       # Dipendenze Python
├── Dockerfile            # Configurazione Docker
├── railway.json          # Configurazione Railway
└── README.md             # Documentazione
```

## 🔍 Logging

Il bot genera log dettagliati in:
- Console (stdout)
- File `bot.log`

Livelli di log:
- **INFO**: Operazioni normali
- **ERROR**: Errori gestiti
- **DEBUG**: Informazioni dettagliate (per sviluppo)

## 🛡️ Sicurezza

- Validazione input utente con Pydantic
- Gestione errori API comprehensive
- Cleanup automatico file temporanei audio
- Variabili d'ambiente per credenziali sensibili

## 🐛 Troubleshooting

### Errori Comuni

1. **Bot non risponde**
   - Verifica il token Telegram
   - Controlla i log per errori API

2. **Audio non generato**
   - Verifica API key ElevenLabs
   - Controlla il Voice ID

3. **Calendario non funziona**
   - Verifica il JSON del service account
   - Assicurati che il calendario sia condiviso
   - Controlla il Calendar ID

4. **Deploy fallisce**
   - Verifica tutte le variabili d'ambiente
   - Controlla i log Railway

### Debug Locale

```bash
# Avvia con log debug
export LOG_LEVEL=DEBUG
python main.py
```

## 📧 Supporto

Per problemi o domande:
1. Controlla i log dell'applicazione
2. Verifica la configurazione delle API
3. Consulta la documentazione delle API esterne

## 🔄 Aggiornamenti

Il bot è progettato per essere facilmente estendibile:
- Aggiungi nuovi servizi in `services/`
- Modifica le fasi conversazione in `bot_handler.py`
- Estendi i modelli dati in `models.py`

## 📄 Licenza

Progetto sviluppato per uso interno del servizio clienti. 