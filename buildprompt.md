Build a web application similar to Google Meet where:

A host can create a meeting link.

Other users can join the meeting using the link.

Each user sets their preferred native language and chooses a voice avatar (e.g., English with American female voice, Yoruba with Nigerian male voice).

When the meeting starts, a translation agent is automatically spawned for each user.

Each agent listens to all other participants’ audio.

Converts speech to text (STT) in the speaker’s language.

Translates it into the listener’s native language.

Synthesizes it into audio using the listener’s chosen voice avatar.

Routes that audio only to the listener.

The app should provide:

A frontend where users can see/join rooms and configure their profile (language + voice).

A backend that manages rooms, generates LiveKit tokens, and runs per-user translation workers.

An API for creating/updating profiles, listing available voices, and generating meeting tokens.

The system must scale so each user runs in an isolated pipeline, ensuring:

Personalized translations.

Fault tolerance if one agent fails.

Customization of tone (formal vs. conversational) and emotional preservation.

The final deliverable should be a full-stack web app with:

Frontend: A simple interface (React/Next.js or similar) where users can:

Create/join meetings.

Set their voice + language.

View live participants.

Backend: FastAPI/Node.js service integrated with LiveKit, Deepgram (STT), OpenAI (translation), ElevenLabs (TTS).

Real-time translation pipeline per user, based on the provided Python backend pattern (Pattern B).

Deployment notes for scaling workers (Kubernetes / LiveKit Cloud).