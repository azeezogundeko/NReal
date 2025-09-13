# Speech.app - Real-time Voice Translation Platform

A modern real-time voice call room UI built with React, TypeScript, and LiveKit that enables seamless global communication through AI-powered voice translation and dubbing.

## 🚀 Features

- **Real-time Voice Communication**: High-quality peer-to-peer voice calls using LiveKit
- **Live Translation**: AI-powered real-time translation between multiple languages
- **Voice Agent Dubbing**: AI agents can dub conversations in real-time for different languages
- **Avatar System**: Customizable voice avatars with different personality types
- **Modern UI**: Beautiful, responsive interface built with Tailwind CSS and Framer Motion
- **Multi-language Support**: Support for 12+ languages including English, Spanish, French, German, Japanese, Chinese, and more

## 🛠️ Tech Stack

- **Frontend**: React 19, TypeScript
- **Real-time Communication**: LiveKit Components React
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Routing**: React Router DOM
- **Build Tool**: Create React App

## 📦 Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd agent_ui
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp env.example .env.local
```

Edit `.env.local` and configure your LiveKit server settings:
```env
REACT_APP_LIVEKIT_URL=ws://localhost:7880
REACT_APP_LIVEKIT_API_KEY=your_api_key_here
REACT_APP_LIVEKIT_SECRET_KEY=your_secret_key_here
```

4. Start the development server:
```bash
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

## 🎯 How to Use

1. **Enter Your Details**: On the home page, enter your name and select your preferred language
2. **Choose an Avatar**: Select a voice avatar that matches your personality
3. **Join or Create Room**: Either join an existing room with a room ID or create a new one
4. **Start Talking**: Once in the room, start talking - the AI will handle real-time translation
5. **Configure Translation**: Use the translation panel to enable/disable voice agent dubbing

## 🌍 Supported Languages

- 🇺🇸 English
- 🇪🇸 Spanish  
- 🇫🇷 French
- 🇩🇪 German
- 🇮🇹 Italian
- 🇵🇹 Portuguese
- 🇷🇺 Russian
- 🇯🇵 Japanese
- 🇰🇷 Korean
- 🇨🇳 Chinese
- 🇸🇦 Arabic
- 🇮🇳 Hindi

## 🎭 Avatar Types

- **Alex (Default)**: Neutral, balanced voice
- **Morgan (Professional)**: Formal, business-appropriate tone
- **Sam (Friendly)**: Warm and approachable voice
- **Jordan (Confident)**: Strong and assertive delivery
- **Riley (Gentle)**: Soft and calming tone
- **Casey (Energetic)**: Upbeat and dynamic voice

## 🏗️ Architecture

The application follows a modular architecture:

```
src/
├── components/          # Reusable UI components
│   ├── AvatarSelector.tsx
│   ├── ConnectionStatus.tsx
│   ├── LanguageSelector.tsx
│   ├── ParticipantTile.tsx
│   ├── TranslationPanel.tsx
│   ├── VoiceCallRoom.tsx
│   └── VoiceControls.tsx
├── pages/              # Route components
│   ├── HomePage.tsx
│   └── RoomPage.tsx
└── App.tsx            # Main application component
```

## 🔧 Key Components

- **HomePage**: Landing page with user configuration
- **RoomPage**: Main room interface with LiveKit integration
- **VoiceCallRoom**: Core voice call functionality
- **ParticipantTile**: Individual participant display with avatar and translation
- **TranslationPanel**: Real-time translation message display
- **VoiceControls**: Audio controls and room management

## 🚀 Deployment

Build the app for production:

```bash
npm run build
```

The build folder contains the production-ready files that can be deployed to any static hosting service.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [LiveKit](https://livekit.io/) for the real-time communication infrastructure
- [Tailwind CSS](https://tailwindcss.com/) for the styling system
- [Framer Motion](https://www.framer.com/motion/) for smooth animations
