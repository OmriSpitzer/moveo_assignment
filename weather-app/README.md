# Weather Risk chat

![React 19.2.8](https://img.shields.io/badge/React-19.2.8-61DAFB?style=for-the-badge&logo=react&logoColor=black) ![TypeScript 6.0.2](https://img.shields.io/badge/TypeScript-6.0.2-3178C6?style=for-the-badge&logo=typescript&logoColor=white) ![Vite 8.3.0](https://img.shields.io/badge/Vite-8.3.0-646CFF?style=for-the-badge&logo=vite&logoColor=white) ![Tailwind CSS 4.3.3](https://img.shields.io/badge/Tailwind_CSS-4.3.3-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white) 

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
src/components/VoiceInput.tsx       English microphone, words stream into the text box
src/services/api.ts                 GET /api/hubs, POST /api/agent/stream
src/services/chat.ts                stream events become the visible tool step
src/types/                          hub, chat, and agent event types
```



## Chat behavior

- Suggestion buttons appear on an empty chat, and only after hubs have loaded. Each question is written from those hubs.
- The hub picker keeps the chosen city and tints its background. The city is not written into the text box.
- Send does nothing when the text box is empty.
- If the typed question does not already name the chosen hub, that hub is added to the message sent to the agent.
- The Mic button opens English speech recognition. Words appear in the text box as they are heard. A pause ends the take and sends it. A click while listening stops the take and leaves the text in the box.
- While a tool is running, the assistant card shows that step. The step disappears when the answer arrives.
- A hub score that changed appears in a yellow list beside the chat. The list scrolls on its own. Each notice leaves after a few seconds, and the chat stays where it was.

Project docs: [README](../README.md), [architecture](../docs/architecture.md), [agent sessions](../docs/conversations/README.md).

