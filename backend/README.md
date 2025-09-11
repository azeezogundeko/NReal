# Translation Service Backend

A real-time translation service built with LiveKit, FastAPI, and AI providers for seamless multilingual communication.

## Features

- **Real-time Translation**: LiveKit-powered translation agents for instant speech translation
- **Multi-language Support**: Support for English, Igbo, Yoruba, and Hausa
- **Voice Avatars**: Custom voice synthesis with ElevenLabs and OpenAI TTS
- **Per-user Customization**: Individual language preferences and voice settings
- **Database Persistence**: Supabase-powered data persistence with real-time sync
- **RESTful API**: FastAPI-based API for room management and user profiles
- **Production Ready**: Comprehensive error handling, logging, and monitoring

## Project Structure

```
backend/
├── app/                    # Main application package
│   ├── api/               # API layer
│   ├── core/              # Core functionality (config, logging)
│   ├── models/            # Data models (domain and pydantic)
│   ├── services/          # Business logic services
│   └── main.py           # FastAPI app factory
├── agents/               # LiveKit worker agents
├── scripts/              # Startup scripts
├── tests/               # Test suite
├── docker/              # Docker configuration
└── requirements.txt     # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.9+
- Supabase account and project
- LiveKit server (Cloud or self-hosted)
- API keys for:
  - OpenAI
  - ElevenLabs
  - Deepgram
  - Supabase (URL and API keys)

### Installation

1. Clone the repository:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Set up the database:
```bash
# Go to your Supabase project dashboard
# Navigate to SQL Editor
# Copy and paste the contents of docs/SUPABASE_SETUP.sql
# Click Run to execute the SQL commands
```

### Running the Application

1. Start the API server:
```bash
python scripts/run_api_server.py
```

2. In a separate terminal, start the LiveKit worker:
```bash
python scripts/run_worker.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Rooms
- `POST /api/rooms` - Create a new room
- `GET /api/rooms` - List all rooms
- `GET /api/rooms/{room_id}` - Get room details

### Profiles
- `POST /api/profiles` - Create user profile
- `GET /api/profiles/{user_id}` - Get user profile
- `PUT /api/profiles/{user_id}/voice` - Update voice avatar

### Voices
- `GET /api/voices` - List available voice avatars

### Tokens
- `POST /api/token` - Generate LiveKit room token

## Configuration

The application uses environment variables for configuration. See `.env.example` for all available options.

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### Type Checking
```bash
mypy .
```

## Deployment

### Docker
```bash
docker-compose up -d
```

### Production Considerations

- Use environment-specific configuration files
- Set up proper logging and monitoring
- Configure CORS for your frontend domain
- Use a production WSGI server (Gunicorn)
- Set up database persistence for production use

## Architecture

The service uses a per-user agent architecture:

1. **API Server**: Handles room creation, user profiles, and token generation
2. **Translation Agents**: LiveKit workers that handle real-time translation for each user
3. **AI Services**: Integration with OpenAI (translation), ElevenLabs (TTS), and Deepgram (STT)

Each user gets their own translation agent that:
- Listens to other participants
- Translates speech to the user's preferred language
- Synthesizes translated audio with their chosen voice avatar

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
