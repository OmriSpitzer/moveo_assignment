# Weather Risk chat

React client for the weather-risk agent. The UI does not call weather, hazard, or geocoding APIs. Hub lists and answers come from the FastAPI service through the Vite `/api` proxy.

## Stack

React 19, TypeScript, Vite 8, Tailwind CSS 4, React Compiler.

## Scripts

```bash
npm install
npm run dev       # local app, proxies /api
npm run build     # tsc -b && vite build
npm run lint
npm run preview
```

`vite.config.ts` sends `/api` to `API_URL`, or to `http://127.0.0.1:8000`.

## Source

```
src/App.tsx                         session, composer, selected hub
src/components/Header.tsx           title
src/components/ChatDisplay.tsx      message list and empty state
src/components/SuggestionsDisplay.tsx
src/components/MessageCard.tsx      one turn, including the live tool step
src/components/HubsDropUp.tsx       hub picker
src/components/VoiceInput.tsx       English microphone, pause ends the take
src/services/api.ts                 GET /api/hubs, POST /api/agent/stream
src/services/chat.ts                stream events become the visible tool step
src/types/                          hub, chat, and agent event types
```

## Chat behavior

- Suggestion buttons appear on an empty chat, and only after hubs have loaded. Each question is written from those hubs.
- The hub picker keeps the chosen city and tints its background. The city is not written into the text box.
- Send does nothing when the text box is empty.
- If the typed question does not already name the chosen hub, that hub is added to the message sent to the agent.
- The Mic button opens English speech recognition. A short pause inserts the transcript into the text box. Send is still a separate click.
- While a tool is running, the assistant card shows that step. The step disappears when the answer arrives.
