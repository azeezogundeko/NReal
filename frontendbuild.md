LiveKit Docs › Getting started › Installation

---

# Installation

> Learn how to install and set up the @livekit/components-react package for React.

Use your favorite package manager to install the LiveKit Components package and its dependencies:

**yarn**:

```shell
yarn add @livekit/components-react @livekit/components-styles livekit-client

```

---

**npm**:

```shell
npm install @livekit/components-react @livekit/components-styles livekit-client

```

---

**pnpm**:

```shell
pnpm install @livekit/components-react @livekit/components-styles livekit-client

```

> ℹ️ **Note**
> 
> When installing the `@livekit/components-react` npm package, it's important to note that it relies on the `livekit-client` and `@livekit/components-styles` packages. This dependency is necessary for the package to function properly.

---

This document was rendered at 2025-09-12T15:46:37.968Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/installation.md](https://docs.livekit.io/reference/components/react/installation.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

LiveKit Docs › Getting started › Best practices

---

# Best practices

> Recommendations for creating apps using LiveKit React components.

## Use LiveKit components for lower-level features

You can create custom React components for your LiveKit app. For lower-level features (for example, mic toggle), however, LiveKit components are built using utility state handling hooks. LiveKit strongly recommends you use these instead of creating your own implementation because they manage React state handling and have been rigorously tested. Lower-level features include input device toggling, and audio and video tracks:

- [StartAudio](https://docs.livekit.io/reference/components/react/component/startaudio.md)
- [StartMediaButton](https://docs.livekit.io/reference/components/react/component/startmediabutton.md)
- [TrackToggle](https://docs.livekit.io/reference/components/react/component/tracktoggle.md)
- [TrackLoop](https://docs.livekit.io/reference/components/react/component/trackloop.md)

If you do create custom components, use the provided hooks for state. For example, to create a custom mic toggle button, use `useTrackToggle`:

```typescript
const { buttonProps, enabled } = useTrackToggle(props);
  return (
    <button ref={ref} {...buttonProps}>
      {(showIcon ?? true) && getSourceIcon(props.source, enabled)}
      {props.children}
    </button>
  );

```

## Using hooks for current state

LiveKit recommends using [hooks](https://docs.livekit.io/reference/components/react/concepts/building-blocks.md#hooks) to get the most current information about room state. For example, to get a list of active tracks or participants in a room:

- [useParticipants](https://docs.livekit.io/reference/components/react/hook/useparticipants.md)
- [useTracks](https://docs.livekit.io/reference/components/react/hook/usetracks.md)

## Updating props for the LiveKitRoom component

Updating props for the `LiveKitRoom` component should _not_ result in the component being repeatedly unmounted and remounted. This results in `Client initiated disconnect` errors and cause users to be repeatedly disconnected and reconnected to the room.

---

This document was rendered at 2025-09-12T15:49:02.182Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/guide.md](https://docs.livekit.io/reference/components/react/guide.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

LiveKit Docs › Concepts › Building blocks

---

# Building blocks

> A short tour through everything you need to build your next LiveKit app.

## Components

Components are the basic building blocks of your LiveKit application, enriched with additional functionality and LiveKit state. Most components are simply a wrapper around a standard HTML element. This allows you to pass standard HTML attributes like `classNames` and `padding` directly to the underlying HTML element to style it exactly how you want.

### Prefabricated components

Prefabs use components under the hood and add additional features, styles, but also reasonable defaults. They are designed to be opinionated and aren't meant to be extended. Prefabs include the following:

- [VideoConference](https://docs.livekit.io/reference/components/react/component/videoconference.md): This component is the default setup of a classic LiveKit video conferencing app.
- [AudioConference](https://docs.livekit.io/reference/components/react/component/audioconference.md): This component is the default setup of a classic LiveKit audio conferencing app.
- [PreJoin](https://docs.livekit.io/reference/components/react/component/prejoin.md): The PreJoin prefab component is normally presented to the user before he enters a room.
- [ControlBar](https://docs.livekit.io/reference/components/react/component/controlbar.md): The ControlBar prefab component gives the user the basic user interface to control their media devices and leave the room.
- [Chat](https://docs.livekit.io/reference/components/react/component/chat.md): The Chat component adds a basis chat functionality to the LiveKit room. The messages are distributed to all participants in the room.

## Hooks

There are a wide range of React hooks that give you fine-grained control to build the app you want. Some hooks are foundational and are needed for almost every LiveKit app, while others are only needed if you want to build some custom components and go low-level.

The most important and frequently used hooks are the following:

- [useTracks](https://docs.livekit.io/reference/components/react/hook/usetracks.md): The useTracks hook returns an array of current tracks that can be looped, filtered, and processed.
- [useParticipants](https://docs.livekit.io/reference/components/react/hook/useparticipants.md): The useParticipants hook returns all participants (local and remote) of the current room.
- [useConnectionState](https://docs.livekit.io/reference/components/react/hook/useconnectionstate.md): The useConnectionState hook allows you to simply implement your own ConnectionState component.

---

This document was rendered at 2025-09-12T15:49:18.114Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/concepts/building-blocks.md](https://docs.livekit.io/reference/components/react/concepts/building-blocks.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

LiveKit Docs › Concepts › LiveKitRoom component

---

# Room Context Setup

While the `LiveKitRoom` component has historically been used as the root of LiveKit applications, we recommend using the `RoomContext.Provider` directly for more control over room lifecycle and state management. This approach gives you more flexibility while still providing the necessary context for LiveKit components.

```tsx
import * as React from 'react';
import { RoomContext } from '@livekit/components-react';
import { Room } from 'livekit-client';

const MyLiveKitApp = () => {
  const [room] = useState(() => new Room({}));
  
  // You can manage room connection lifecycle here
  useEffect(() => {
    room.connect('your-server-url', 'your-token');
    return () => {
      room.disconnect();
    };
  }, [room]);

  return (
    <RoomContext.Provider value={room}>
      {/* Your components go here */}
    </RoomContext.Provider>
  );
};

```

This pattern offers several advantages:

1. Direct control over Room instantiation and configuration
2. Explicit connection lifecycle management
3. Ability to handle connection states and errors more granularly
4. Better integration with application state management

All LiveKit components that previously worked with `LiveKitRoom` will work identically with this setup, as they rely on the `RoomContext` being available in the component tree.

---

This document was rendered at 2025-09-12T15:49:27.333Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/concepts/livekit-room-component.md](https://docs.livekit.io/reference/components/react/concepts/livekit-room-component.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

LiveKit Docs › Concepts › Contexts

---

# Contexts

> Learn how contexts in LiveKit components provide easy access to the parent state for nested components.

## What is a context

[Contexts](https://react.dev/learn/passing-data-deeply-with-context) are used to allow child components to access parent state without having to pass it down the component tree via props. However, this means that if a component depends on a context, you must make sure that context is provided somewhere up the component tree.

```tsx

// ✅ This works!
// ConnectionState depends on the RoomContext which is provided by LiveKitRoom.
<LiveKitRoom>
  <ConnectionState />
</LiveKitRoom>

// ✅ This works!
// The context provider (LiveKitRoom) does not have to be a immediate parent of the component (ConnectionState) needing the context.
<LiveKitRoom>
    <div>
        <ConnectionState />
    </div>
</LiveKitRoom>

// ❌ This will cause an error!
// ConnectionState depends on a parent component to provide the RoomContext.
<LiveKitRoom></LiveKitRoom>
<ConnectionState />

```

If you only use LiveKit Components without creating custom components yourself, you don't need to interact with the contexts. Just make sure that the component tree meets the context requirements of all components. If it doesn't, you'll get an error message telling you which context is missing.

The two most important contexts are:

## Room context

The `RoomContext` provides the [Room](https://docs.livekit.io/reference/client-sdk-js/classes/Room.html.md) object as a context. While previously this was primarily provided through the `LiveKitRoom` component, we recommend using `RoomContext.Provider` directly:

```tsx
const MyApp = () => {
  const [room] = useState(() => new Room());
  
  useEffect(() => {
    room.connect('server-url', 'user-access-token');
    return () => room.disconnect();
  }, [room]);

  return (
    <RoomContext.Provider value={room}>
      {/* Components that need room context */}
      <ConnectionState />
    </RoomContext.Provider>
  );
};

```

This approach gives you more control over the Room lifecycle while still providing the necessary context for all LiveKit components.

## Participant context

The `ParticipantContext` provides a [Participant](https://docs.livekit.io/client-sdk-js/classes/Room.html) object to all child components.

```tsx
/* 1️⃣ ParticipantTile provides the ParticipantContext. */
<ParticipantTile>
  {/* 2️⃣ ParticipantName uses the ParticipantContext to get the participant name. */}
  <ParticipantName />
</ParticipantTile>

```

## Accessing contexts

Context access is not required to build an application using LiveKit Components. However, if you want to build custom components that depend on a context, you can use one of the hooks we provide. For example, you can use the [`useRoomContext`](https://docs.livekit.io/reference/components/react/hook/useroomcontext.md) hook to access the `Room` object and the [`useParticipantContext`](https://docs.livekit.io/reference/components/react/hook/useparticipantcontext.md) hook to access the `Participant` object.

---

This document was rendered at 2025-09-12T15:49:36.912Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/concepts/contexts.md](https://docs.livekit.io/reference/components/react/concepts/contexts.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

LiveKit Docs › Concepts › Loop components

---

# Loop Components

Loop components are a thin layer on top of basic JS for-loops, creating a dedicated React context (`TrackRefContext` or `ParticipantContext`) on each iteration. They accept a child component to use as a template for all elements of the passed array.

## Track Loop

The `TrackLoop` component loops over an array of `TrackReferences` and creates a `TrackRefContext` for every item. We can use it for example to loop over all camera tracks of the room and render them with the `ParticipantTile` component.

```tsx
const cameraTracks = useTracks([Track.Source.Camera]);

<TrackLoop tracks={cameraTracks}>
  <ParticipantTile />
</TrackLoop>;

```

We can nest any other component inside the loop if we need more flexibility or control. If we want to build our own ParticipantTile for full control over styling, we could do this:

```tsx
function MyParticipantTile() {
  return (
    <div style={{ position: 'relative' }}>
      <TrackRefContext.Consumer>
        {(track) => track && <VideoTrack {...track} />}
      </TrackRefContext.Consumer>
    </div>
  );
}

```

And then pass it as a template to the `TrackLoop`.

```tsx
const cameraTracks = useTracks([Track.Source.Camera]);

<TrackLoop tracks={cameraTracks}>
  <MyParticipantTile />
</TrackLoop>;

```

> 💡 **Tip**
> 
> How is this different from the `ParticipantLoop`? One Participant can have more than one Track. E.g. it is not uncommon to loop over all camera as well as screen share tracks.

For more details check out the [TrackLoop](https://docs.livekit.io/reference/components/react/component/trackloop.md) page.

## Participant Loop

The `ParticipantLoop` component loops over an array of Participants and creates a distinct `ParticipantContext` for each child. As an example, to render a list of all the participants' names in the room, we could simply do the following:

```tsx
import { useParticipants, ParticipantLoop, ParticipantName } from `@livekit/react`;

const participants = useParticipants();

<ParticipantLoop participants={participants}>
  // ParticipantName is a LiveKit component that uses the ParticipantContext
  // to render the name of a participant.
  <ParticipantName />
</ParticipantLoop>

```

For more details take a look at the [ParticipantLoop](https://docs.livekit.io/reference/components/react/component/participantloop.md) API page.

## Filter Loops

In order to loop over only a subset of the tracks, you will need to filter the tracks before passing them as a property to the `TrackLoop`. Use the standard [Array.filter()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/filter) function to do so.

```tsx
const tracks = useTracks([
  { source: Track.Source.Camera, withPlaceholder: true },
  { source: Track.Source.ScreenShare, withPlaceholder: false },
]);

const screenShareTracks = tracks.filter(
  (track) => track.publication.source === Track.Source.ScreenShare,
);

// Loop only over screen share tracks.
<TrackLoop tracks={screenShareTracks}>
  <ParticipantTile />
</TrackLoop>;

```

## Default Template

Both loops have in common that they only accept one or no child. If no child is provided the default template is used. If a child is provided, it is used as a template for every item of the loop.

```tsx
// TrackLoop will use the default template.
<TrackLoop trackRefs={tracks}/>

// TrackLoop will use MyComponent as a template.
<TrackLoop trackRefs={tracks}>
  <MyComponent />
</TrackLoop>

```

---

This document was rendered at 2025-09-12T15:49:45.729Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/concepts/loops.md](https://docs.livekit.io/reference/components/react/concepts/loops.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

LiveKit Docs › Concepts › Custom components

---

# Custom Components

We try to offer a comprehensive set of components that allow you to build something valuable quickly. But we are aware that it would be utopian to think that a limited set of components can cover all wishes and ideas. This is why we made extensibility and customization a central part of LiveKit Components.

## React hooks

Almost every component is accompanied by a React hook with the same name, prefixed with the word `use`. For example, the `ConnectionQualityIndicator` is being built with the `useConnectionQualityIndicator` hook. The same hooks that are used to create LiveKit components can also be used for custom components.

## Custom component example

The best way to see how easy it is to create a custom component is to give a quick example. Let's create a "CustomConnectionQualityIndicator" to replace the existing "ConnectionQualityIndicator".

The default indicator uses icons to indicate how good a subscriber's connection quality is, and we could use it like this:

```tsx
//...
<ParticipantTile>
  <ParticipantName />
  <ConnectionQualityIndicator />
</ParticipantTile>
//...

```

This would display the name of the participant and the quality of the connection as a icon. Suppose that instead of an icon representation, we want a textual representation of the connection status. If a user Ana has a good connection quality, we want it to say "Ana has a good connection quality".

This can be easily achieved with a custom LiveKit component:

```tsx
// 1️⃣ Import the react hook.
import { useConnectionQualityIndicator } from '@livekit/components-react';

// 2️⃣ Define a custom React component.
export function CustomConnectionQualityIndicator(props: HTMLAttributes<HTMLSpanElement>) {
  /**
   * 3️⃣ By using this hook, we inherit all the state management and logic and can focus on our
   * implementation.
   */
  const { quality } = useConnectionQualityIndicator();

  // We create a little helper function to convert the ConnectionQuality to a string.
  function qualityToText(quality: ConnectionQuality): string {
    switch (quality) {
      case ConnectionQuality.Unknown:
        return 'unknown';
      case ConnectionQuality.Poor:
        return 'poor';
      case ConnectionQuality.Good:
        return 'good';
      case ConnectionQuality.Excellent:
        return 'excellent';
    }
  }

  return <span {...props}>{` has a ${qualityToText(quality)} connection quality.`} </span>;
}

```

Now we can replace the default quality indicator with our new `CustomConnectionQualityIndicator` as follows:

```tsx
//...
<ParticipantTile>
  <ParticipantName />
  {/* Custom component: Here we replace the provided <ConnectionQualityIndicator />  with our own implementation. */}
  <CustomConnectionQualityIndicator />
</ParticipantTile>
//...

```

As you can see, it's super easy to create your own components in no time. 🚀

> 💡 **Tip**
> 
> If you want to replace a component, as we did here. Often the quickest way is to copy the current implementation and use it as a starting point for your implementation.

---

This document was rendered at 2025-09-12T15:49:57.436Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/concepts/custom-components.md](https://docs.livekit.io/reference/components/react/concepts/custom-components.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

LiveKit Docs › Concepts › Style components

---

# Styling LiveKit Components

## Our approach to styling

All LiveKit components come with carefully designed and beautiful styles that you can use right out of the box. If you're happy with the default styles, that's perfect, but if not, we've got you covered too! We do everything we can to give you the freedom to simply override, extend and change the styles to your liking.

## Use the default LiveKit theme

To add styling from our `@livekit/components-styles` package install and import it.

```ts
import '@livekit/components-styles';

```

Our carefully crafted default theme can be applied by adding the data attribute `data-lk-theme="default"` to the `<LiveKitRoom/>` or any HTML container. This will provide all LiveKit components with their default styles and give you access to the theme.

```tsx
// 🅰️ Set the scope of the theme directly on the `LiveKitRoom` component
<LiveKitRoom data-lk-theme="default" >
  {/* Use the color defined in LiveKit default theme. */}
  <button style={{ background: 'var(--lk-danger)' }} >My Button</button>
</LiveKitRoom>

// 🅱️ or on any regular HTML element.
<div data-lk-theme="default" >
  <LiveKitRoom >
  </LiveKitRoom>
</div>


```

## Style LiveKit Components like a HTML element

Almost all LiveKit components are built on a basic HTML element. For example, the `TrackMutedIndicator` component is just a div with some hooks that deal with status (e.g. whether a camera track is muted or not). This means that you can treat the `TrackMutedIndicator` component like a div and pass `className` or `style` properties to apply styling.

```tsx
// Apply custom styling like you would with a regular div element.
<TrackMutedIndictor className="your-classes" style={{ padding: '1rem' }} />

```

## Change global color pallet

All components share a small but carefully selected color palette. Each color from the palette is saved as a CSS custom property (CSS variable). You can find the palette [here](https://github.com/livekit/components-js/blob/main/packages/styles/scss/themes/default.scss). Override them as you normally would with CSS custom properties to customize them to your liking.

```css
/* Excerpt of the color palette  */
:root {
  --lk-fg: #111;
  --lk-fg-secondary: #333;
  --lk-fg-tertiary: #555;

  --lk-bg: #fff;
  --lk-bg-secondary: #f5f5f5;
  --lk-bg-tertiary: #fafafa;

  --lk-accent-fg: #fff;
  --lk-accent-bg: #1f8cf9;

  --lk-danger-fg: #fff;
  --lk-danger: #f91f31;
  --lk-danger-text: #6d0311;
  --lk-danger-bg: #fecdd4;

  --lk-success-fg: #fff;
  --lk-success: #1ff968;
  --lk-success-text: #036d26;
  --lk-success-bg: #cdfedd;

  --lk-control-fg: var(--fg);
  --lk-control-bg: var(--bg-secondary);

  --lk-connection-excellent: #06db4d;
  --lk-connection-good: #f9b11f;
  --lk-connection-poor: #f91f31;
  ...

```

## Use of HTML custom data attributes in LiveKit Components

[Custom data attributes](https://developer.mozilla.org/en-US/docs/Learn/HTML/Howto/Use_data_attributes) are an easy way to store additional information on standard HTML elements. We use data attributes on many elements to show what state the component is in, or to provide additional information that can be used for styling.

> 💡 **Tip**
> 
> All data attributes in LiveKit Components start with `data-lk-`

For example, the `ConnectionQualityIndicator` shows the connection quality of a participant. The component renders an HTML div element and we add the custom data attribute `data-lk-quality` to it. The value of the custom data attribute is updated according to the current connection quality and can take the values "unknown", " poor", "good" and "excellent".

```tsx
// Participant with a excellent connection.
<div data-lk-quality="excellent">
  {/* ... */}
</div>

// Participant with a poor connection.
<div data-lk-quality="poor">
  {/* ... */}
</div>

```

The data attributes are simple HTML attributes, so we can access them via CSS. For example, to update the ConnectionQualityIndicator background, we can use the attribute selector to change the styles according to the value of the data attribute:

```css
[data-lk-quality='excellent'] {
  background-color: green;
}
[data-lk-quality='poor'] {
  background-color: red;
}

```

> 💡 **Tip**
> 
> Currently it is not documented which data attribute is used for which component. At the moment it is best to open the inspector and check which data attribute is used.

---

This document was rendered at 2025-09-12T15:50:09.260Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/concepts/style-components.md](https://docs.livekit.io/reference/components/react/concepts/style-components.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

LiveKit Docs › Concepts › Rendering video tracks

---

# Rendering a single track

To demonstrate how to build a UI to render a single video stream, imagine this scenario:

We have a LiveKit Room with three Participants who are constantly streaming a camera feed into the room. In our example, the Participants are not human, but webcams streaming from "Berlin", "New York" and "Tokyo". For unknown reasons, we only want to see the stream from "Tokyo".

We start by creating a new React component and get all the camera tracks with `useTracks([Track.Source.Camera])`. In the returned array of `TrackReferences` we look for the Tokyo stream. Since we know that all webcam participants are named after their cities, we look for the `tokyo` participant.

```tsx
import { useTracks } from '@livekit/components-react';
import { Track } from 'livekit-client';

function CityVideoRenderer() {
  const trackRefs = useTracks([Track.Source.Camera]);
  const tokyoCamTrackRef = trackRefs.find((trackRef) => trackRef.participant.name === 'tokyo');

  return <>TODO</>;
}

```

Now that we have found the correct stream, we can move on to building the UI to display it. We can do this by importing the `VideoTrack` component and passing it the track reference. If the Tokyo track reference is not found, we will display a UI to indicate this instead.

```tsx
import { useTracks, VideoTrack } from '@livekit/components-react';
import { Track } from 'livekit-client';

function CityVideoRenderer() {
  const trackRefs = useTracks([Track.Source.Camera]);
  const tokyoCamTrackRef = trackRefs.find((trackRef) => trackRef.participant.name === 'tokyo');

  return (
    <>
      {tokyoCamTrackRef ? <VideoTrack trackRef={tokyoCamTrackRef} /> : <div>Tokyo is offline</div>}
    </>
  );
}

```

With our UI in place, we need to provide useTracks with the proper context to return the tracks of a LiveKit Room. We do this by nesting everything inside the `<LiveKitRoom>` component.

```tsx
import { LiveKitRoom, useTracks, VideoTrack } from '@livekit/components-react';
import { Track } from 'livekit-client';

function CityVideoRenderer() {
  const trackRefs = useTracks([Track.Source.Camera]);
  const tokyoCamTrackRef = trackRefs.find((trackRef) => trackRef.participant.name === 'tokyo');

  return (
    <>
      {tokyoCamTrackRef ? <VideoTrack trackRef={tokyoCamTrackRef} /> : <div>Tokyo is offline</div>}
    </>
  );
}

function MyPage() {
  return (
    <LiveKitRoom>
      <CityVideoRenderer />
    </LiveKitRoom>
  );
}

```

---

This document was rendered at 2025-09-12T15:50:19.607Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/concepts/rendering-video.md](https://docs.livekit.io/reference/components/react/concepts/rendering-video.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

LiveKit Docs › Concepts › Rendering audio tracks

---

# Audio rendering with React Components

> Different ways to render audio with React Components

There are two primary methods for rendering (making audio tracks audible) audio with React Components, each offering distinct benefits and suited for different use cases.

## Render all audio tracks within the room

The [`RoomAudioRenderer`](https://docs.livekit.io/reference/components/react/component/roomaudiorenderer.md) component simplifies audio management in LiveKit Rooms by rendering all audio tracks together. It's a straightforward and often optimal solution. Just import `RoomAudioRenderer` and place it in your `LiveKitRoom` component for seamless audio integration.

```tsx
<LiveKitRoom audio={true} video={true} token={token}>
  <RoomAudioRenderer />
</LiveKitRoom>

```

> 💡 **Tip**
> 
> Utilizing the `RoomAudioRenderer` ensures automatic benefits from future server side performance enhancements without requiring any modifications to your existing code.

## Full control and ownership of the audio rendering process

For complete control over individual audio Tracks, including muting and volume adjustments at the track level, you can craft a custom audio renderer using the [`useTracks`](https://docs.livekit.io/reference/components/react/hook/usetracks.md) hook alongside the [`<AudioTrack/>`](https://docs.livekit.io/reference/components/react/component/audiotrack.md) component. For example, this level of control can be used to create spatial audio applications where you may want to adjust each audio track based on the distance between participants.

```js
  const tracks = useTracks([
    Track.Source.Microphone,
    Track.Source.ScreenShareAudio,
    Track.Source.Unknown,
  ]).filter((ref) => !isLocal(ref.participant) && ref.publication.kind === Track.Kind.Audio);

  return (
    <div style={{ display: 'none' }}>
      {tracks.map((trackRef) => (
        <AudioTrack
          key={getTrackReferenceId(trackRef)}
          trackRef={trackRef}
          volume={volume}
          muted={muted}
        />
      ))}
    </div>
  );

```

Depending on your application it is possible that audio tracks have an unknown source. To render these as well, we include the `Track.Source.Unknown` in the array of sources passed to the `useTracks` hook, but then filter out the tracks that are not of kind `Audio`.

---

This document was rendered at 2025-09-12T15:50:31.634Z.
For the latest version of this document, see [https://docs.livekit.io/reference/components/react/concepts/rendering-audio.md](https://docs.livekit.io/reference/components/react/concepts/rendering-audio.md).

To explore all LiveKit documentation, see [llms.txt](https://docs.livekit.io/llms.txt).

useChat
The useChat hook provides chat functionality for a LiveKit room.

Import
import { useChat } from "@livekit/components-react";

Remarks
Message history is not persisted and will be lost if the component is refreshed. You may want to persist message history in the browser, a cache or a database.

Usage
function ChatComponent() {
  const { chatMessages, send, isSending } = useChat();

  return (
    <div>
      {chatMessages.map((msg) => (
        <div key={msg.timestamp}>
          {msg.from?.identity}: {msg.message}
        </div>
      ))}
      <button disabled={isSending} onClick={() => send("Hello!")}>
        Send Message
      </button>
    </div>
  );
}

Returns
An object containing: - chatMessages - Array of received chat messages - send - Function to send a new message - isSending - Boolean indicating if a message is currently being sent

{
    send: (message: string, options?: import('livekit-client').SendTextOptions) => Promise<ReceivedChatMessage>;
    chatMessages: ReceivedChatMessage[];
    isSending: boolean;
}

useChatToggle
The useChatToggle hook provides state and functions for toggling the chat window.

Import
import { useChatToggle } from "@livekit/components-react";

Remarks
Depends on the LayoutContext to work properly.

Properties
{ props }.props
React.ButtonHTMLAttributes<HTMLButtonElement>
Required
Returns
{
    mergedProps: React.ButtonHTMLAttributes<HTMLButtonElement> & {
        className: string;
        onClick: () => void;
        'aria-pressed': string;
        'data-lk-unread-msgs': string;
    };
}

On this page

Import
Remarks
Properties
Returns

useClearPinButton
The useClearPinButton hook provides props for the ClearPinButton() or your custom implementation of it component. It adds the onClick handler to signal the LayoutContext that the tile in focus should be cleared.

Import
import { useClearPinButton } from "@livekit/components-react";

Returns
{
    buttonProps: ClearPinButtonProps & {
        className: string;
        disabled: boolean;
        onClick: () => void;
    };
}

On this page

Import
Returns

useConnectionQualityIndicator
The useConnectionQualityIndicator hook provides props for the ConnectionQualityIndicator or your custom implementation of it component.

Import
import { useConnectionQualityIndicator } from "@livekit/components-react";

Usage
const { quality } = useConnectionQualityIndicator();
// or
const { quality } = useConnectionQualityIndicator({ participant });

Properties
options.participant
Participant
Optional
Returns
{
  className: "lk-connection-quality";
  quality: import("livekit-client").ConnectionQuality;
}

useConnectionState
The useConnectionState hook allows you to simply implement your own ConnectionState component.

Import
import { useConnectionState } from "@livekit/components-react";

Usage
const connectionState = useConnectionState(room);

Properties
room
Room
Optional
Returns
import("livekit-client").ConnectionState;

On this page

Import
Usage
Properties
Returns

useCreateLayoutContext
Import
import { useCreateLayoutContext } from "@livekit/components-react";

Returns
LayoutContextType;

useDataChannel
The useDataChannel hook returns the ability to send and receive messages. Pass an optional topic to narrow down which messages are returned in the messages array.

Import
import { useDataChannel } from "@livekit/components-react";

Remarks
There is only one data channel. Passing a topic does not open a new data channel. It is only used to filter out messages with no or a different topic.

Usage
Example 1
// Send messages to all participants via the 'chat' topic.
const { message: latestMessage, send } = useDataChannel("chat", (msg) =>
  console.log("message received", msg)
);

Example 2
// Receive all messages (no topic filtering)
const { message: latestMessage, send } = useDataChannel((msg) =>
  console.log("message received", msg)
);

Properties
topic
T
Required
onMessage
(msg: ReceivedDataMessage<T>) => void
Optional
Returns
UseDataChannelReturnType<T>;

AudioConference
This component is the default setup of a classic LiveKit audio conferencing app. It provides functionality like switching between participant grid view and focus view.

Import
import { AudioConference } from "@livekit/components-react";

Remarks
The component is implemented with other LiveKit components like FocusContextProvider, GridLayout, ControlBar, FocusLayoutContainer and FocusLayout.

Usage
<LiveKitRoom>
  <AudioConference />
<LiveKitRoom>

AudioTrack
The AudioTrack component is responsible for rendering participant audio tracks. This component must have access to the participant's context, or alternatively pass it a Participant as a property.

Import
import { AudioTrack } from "@livekit/components-react";

Usage
<ParticipantTile>
  <AudioTrack trackRef={trackRef} />
</ParticipantTile>

Properties
muted
boolean
Optional
(Optional) Mutes the audio track if set to true.

onSubscriptionStatusChanged
(subscribed: boolean) => void
Optional
(Optional)

trackRef
TrackReference
Optional
(Optional) The track reference of the track from which the audio is to be rendered.

volume
number
Optional
(Optional) Sets the volume of the audio track. By default, the range is between 0.0 and 1.0.

On this page

Import
Usage
Properties
Is this page helpful?



Previous

Visualizes audio signals from a TrackReference as bars. If the state prop is set, it automatically transitions between VoiceAssistant states.

Import
import { BarVisualizer } from "@livekit/components-react";

Remarks
For VoiceAssistant state transitions this component requires a voice assistant agent running with livekit-agents >= 0.9.0

Usage
Example 1
function SimpleVoiceAssistant() {
  const { state, audioTrack } = useVoiceAssistant();
  return <BarVisualizer state={state} trackRef={audioTrack} />;
}

Styling the BarVisualizer using CSS classes
.lk-audio-bar {
 // Styles for "idle" bars
 }
.lk-audio-bar.lk-highlighted {
 // Styles for "active" bars
}

Styling the BarVisualizer using CSS custom properties
--lk-fg // for the "active" colour, note that this defines the main foreground colour for the whole "theme"
--lk-va-bg // for "idle" colour

Using a custom bar template for the BarVisualizer
<BarVisualizer>
  <div className="all the classes" />
</BarVisualizer>

the highlighted children will get a data prop of data-lk-highlighted for them to switch between active and idle bars in their own template 


Pictographic representation of the component.
CarouselLayout
The CarouselLayout component displays a list of tracks in a scroll container. It will display as many tiles as possible and overflow the rest.

Import
import { CarouselLayout } from "@livekit/components-react";

Remarks
To ensure visual stability when tiles are reordered due to track updates, the component uses the useVisualStableUpdate hook.

Usage
const tracks = useTracks([Track.Source.Camera]);
<CarouselLayout tracks={tracks}>
  <ParticipantTile />
</CarouselLayout>;

Properties
children
React.ReactNode
Required
tracks
TrackReferenceOrPlaceholder[]
Required
orientation
'vertical' | 'horizontal'
Optional
(Optional) Place the tiles vertically or horizontally next to each other. If undefined orientation is guessed by the dimensions of the container.