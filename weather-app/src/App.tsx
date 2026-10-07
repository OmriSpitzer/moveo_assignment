import { useEffect, useState, type SubmitEvent, type KeyboardEvent } from 'react'
import { ChatDisplay } from './components/ChatDisplay'
import { Header } from './components/Header'
import HubsDropUp from './components/HubsDropUp'
import { fetchHubs, streamAgent } from './services/api'
import { applyEvent } from './services/chat'
import type { ChatMessage, Hub } from './types'

/**
 * Main app component
 * 
 * @description Overall app layout and state management for the weather app
 */
const App = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])       // Chat messages
  const [input, setInput] = useState('')                            // User input
  const [isStreaming, setIsStreaming] = useState(false)             // Streaming state
  const [threadId] = useState(() => crypto.randomUUID())            // Thread ID
  const [hubs, setHubs] = useState<Hub[]>([])                       // Hubs
  const [hubsError, setHubsError] = useState(false)                 // Hubs error
  const [selectedHub, setSelectedHub] = useState('')                // Selected hub

  // Retrieve hubs from server
  const loadHubs = async () => {
    try {
      setHubs(await fetchHubs())
      setHubsError(false)
    } catch {
      setHubsError(true)
    }
  }

  // Load hubs on component mount
  useEffect(() => {
    void loadHubs()
  }, [])

  // Update the last message in the chat history
  const updateLast = (update: (message: ChatMessage) => ChatMessage) =>
    setMessages((prev) => [...prev.slice(0, -1), update(prev[prev.length - 1])])

  // Send a message to the agent
  const send = async (text: string) => {
    const question = text.trim()
    if (!question || isStreaming) return

    // Build the chat history
    const history = [
      ...messages.filter((m) => !m.error && m.content).map(({ role, content }) => ({ role, content })),
      { role: 'user' as const, content: question },
    ]

    // Update the chat history
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question, steps: [] },
      { role: 'assistant', content: '', steps: [] },
    ])

    // Clear the input and set the streaming state to true
    setInput('')
    setIsStreaming(true)

    // Stream the agent response
    try {
      await streamAgent(history, threadId, (event) => updateLast((m) => applyEvent(m, event)))
    } catch (e) {
      updateLast((m) => ({ ...m, content: e instanceof Error ? e.message : String(e), error: true }))
    } finally {
      setIsStreaming(false)
      void loadHubs()
    }
  }

  // Send the input, adding the selected hub when the text does not name it
  const sendInput = () => {
    const typed = input.trim()
    if (!typed) return
    const question =
      selectedHub && !typed.toLowerCase().includes(selectedHub.toLowerCase())
        ? `${typed} ${selectedHub}`
        : typed
    void send(question)
  }

  // Handle form submission
  const onSubmit = (e: SubmitEvent) => {
    e.preventDefault()
    sendInput()
  }

  // Handle key down event
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendInput()
    }
  }

  return (
    <div className="flex h-svh flex-col bg-slate-50 text-slate-800">
      {/* Header */}
      <Header />

      {/* Chat display with user */}
      <ChatDisplay messages={messages} hubs={hubs} onSuggest={send} />

      <form onSubmit={onSubmit} className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-3xl items-end gap-2">
          {/* Hubs dropdown */}
          <HubsDropUp hubs={hubs} hubsError={hubsError} selected={selectedHub} onSelect={setSelectedHub} />

          {/* Textarea for user input */}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Ask a me a question..."
            className="max-h-40 flex-1 resize-none rounded-xl border border-slate-300 px-4 py-2 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100"
          />

          {/* Submit button */}
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="rounded-xl bg-sky-600 px-4 py-2 font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {isStreaming ? 'Working…' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default App;
