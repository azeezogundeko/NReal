# Speech.app - Real-time Voice Translation

A React application built with LiveKit components for real-time voice translation during video conferences.

## Features

- **Landing Page**: Simple introduction with Create Room and Join Room options
- **Room Creation**: Generate unique room links with customizable settings
- **Room Joining**: Enter room codes with language preferences
- **Real-time Communication**: Live video/audio with LiveKit components
- **Translation Interface**: Real-time captions and translation display
- **Error Handling**: Comprehensive error pages for various scenarios

## Tech Stack

- **React 18** with TypeScript
- **LiveKit Components** for real-time communication
- **React Router** for navigation
- **CSS Custom Properties** for theming
- **Responsive Design** for mobile and desktop

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

## Project Structure

```
src/
├── pages/
│   ├── LandingPage.tsx      # Home page with create/join options
│   ├── CreateRoomPage.tsx   # Room creation with settings
│   ├── JoinRoomPage.tsx     # Room joining with language selection
│   ├── RoomPage.tsx         # Main communication interface
│   └── ErrorPage.tsx        # Error handling pages
├── App.tsx                  # Main app with routing
├── App.css                  # Global styles and LiveKit theme
└── index.css                # Base styles and reset
```

## LiveKit Integration

This app uses LiveKit components for real-time communication:

- `@livekit/components-react` - React components for LiveKit
- `@livekit/components-styles` - Default styling
- `livekit-client` - Core LiveKit client

### Key Components Used

- `RoomContext.Provider` - Provides room context to child components
- `VideoConference` - Complete video conferencing interface
- `AudioConference` - Audio-only conferencing
- `useTracks` - Hook for accessing media tracks
- `useParticipants` - Hook for participant management
- `useConnectionState` - Hook for connection status

## Features Overview

### 1. Landing Page
- Clean, modern design with feature highlights
- Two main actions: Create Room and Join Room
- Responsive layout for all devices

### 2. Create Room
- Generate unique 9-character room codes
- Language preferences and settings
- Share room links with participants
- Copy to clipboard functionality

### 3. Join Room
- Room code input with validation
- Language selection for translation
- User type selection (Participant/Agent)
- URL parameter support for direct room joining

### 4. Main Room Interface
- Live video conferencing with LiveKit
- Real-time translation display
- Language switching on the fly
- Mute/unmute controls
- Connection status indicators
- Live captions with translation

### 5. Error Handling
- Room not found errors
- Connection issues
- 404 page handling
- User-friendly error messages

## Styling

The app uses LiveKit's default theme with custom CSS variables:

- `--lk-bg` - Background colors
- `--lk-fg` - Foreground colors
- `--lk-accent-bg` - Accent colors
- `--lk-danger` - Error states
- `--lk-success` - Success states

## Development

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App

### Environment Setup

For production deployment, you'll need to:

1. Set up a LiveKit server
2. Configure authentication tokens
3. Update the server URL in RoomPage.tsx
4. Implement backend room management

## Hackathon Notes

This project was built for the Spitch Hackathon with focus on:

- ✅ Core functionality (Landing → Create/Join → Room)
- ✅ LiveKit integration for real-time communication
- ✅ Translation interface mockup
- ✅ Responsive design
- ✅ Error handling
- ⏳ Backend integration (for production)
- ⏳ Real translation service integration

## Future Enhancements

- User authentication and profiles
- Room history and favorites
- Advanced translation settings
- Voice avatar customization
- Recording and playback
- Mobile app version

## License

This project is built for the Spitch Hackathon and is for demonstration purposes.
