import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { fetchHubs, streamAgent, type AgentEvent, type Hub, type Role } from './api'

type Step = { id: string; label: string; done: boolean }

type ChatMessage = {
  role: Role
  content: string
  steps: Step[]
  error?: boolean
}

const TOOL_LABELS: Record<string, string> = {
  list_hubs: 'Reading the hub list',
  score_hubs: 'Scoring hub risk',
  get_location: 'Finding the hub location',
  get_weather_history: 'Reading weather history',
  get_disaster_history: 'Reading disaster history',
  get_active_alerts: 'Checking active alerts',
}

function placeNames(value: unknown): string | null {
  if (!Array.isArray(value) || value.length === 0) return null
  const names = value.flatMap((item) => {
    if (!item || typeof item !== 'object') return []
    const place = item as { city?: unknown; state_code?: unknown }
    if (typeof place.city === 'string') return [place.city]
    if (typeof place.state_code === 'string') return [place.state_code]
    return []
  })
  return names.length > 0 ? names.join(', ') : `${value.length} locations`
}

function stepLabel(name: string, args: Record<string, unknown>): string {
  const label = TOOL_LABELS[name] ?? name
  const places = placeNames(args.places) ?? placeNames(args.points) ?? placeNames(args.cities)
  if (places) return `${label} for ${places}`
  return typeof args.city === 'string' ? `${label}: ${args.city}` : label
}

const SUGGESTIONS = [
  'Which hubs do we operate, by region?',
  'Which Midwest hubs are most exposed to winter disruption?',
  'Compare Miami and Houston for hurricane and flood exposure.',
  'What percentage of days in Denver last year had snowfall?',
  'Which South hubs had the most FEMA disaster declarations since 2000?',
  'Do any of our hubs have active weather alerts right now?',
]

function groupByRegion(hubs: Hub[]): [string, Hub[]][] {
  const groups = new Map<string, Hub[]>()
  for (const hub of hubs) groups.set(hub.region, [...(groups.get(hub.region) ?? []), hub])
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b))
}

function applyEvent(message: ChatMessage, event: AgentEvent): ChatMessage {
  switch (event.type) {
    case 'tool_call':
      return {
        ...message,
        steps: [...message.steps, { id: event.id, label: stepLabel(event.name, event.args), done: false }],
      }
    case 'tool_result':
      return { ...message, steps: message.steps.map((s) => (s.id === event.id ? { ...s, done: true } : s)) }
    case 'answer':
      return { ...message, content: event.answer.answer }
    case 'error':
      return { ...message, content: event.message, error: true }
    default:
      return message
  }
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [threadId] = useState(() => crypto.randomUUID())
  const [hubs, setHubs] = useState<Hub[]>([])
  const [hubsError, setHubsError] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  async function loadHubs() {
    try {
      setHubs(await fetchHubs())
      setHubsError(false)
    } catch {
      setHubsError(true)
    }
  }

  useEffect(() => {
    void loadHubs()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function insertHub(city: string) {
    if (!city) return
    setInput((prev) => (prev.trim() ? `${prev.trimEnd()} ${city}` : city))
  }

  const updateLast = (update: (message: ChatMessage) => ChatMessage) =>
    setMessages((prev) => [...prev.slice(0, -1), update(prev[prev.length - 1])])

  async function send(text: string) {
    const question = text.trim()
    if (!question || isStreaming) return

    const history = [
      ...messages.filter((m) => !m.error && m.content).map(({ role, content }) => ({ role, content })),
      { role: 'user' as const, content: question },
    ]
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question, steps: [] },
      { role: 'assistant', content: '', steps: [] },
    ])
    setInput('')
    setIsStreaming(true)

    try {
      await streamAgent(history, threadId, (event) => updateLast((m) => applyEvent(m, event)))
    } catch (e) {
      updateLast((m) => ({ ...m, content: e instanceof Error ? e.message : String(e), error: true }))
    } finally {
      setIsStreaming(false)
      void loadHubs()
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void send(input)
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send(input)
    }
  }

  return (
    <div className="flex h-svh flex-col bg-slate-50 text-slate-800">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-lg font-semibold text-slate-900">Weather Risk Agent</h1>
          <p className="text-sm text-slate-500">
            Ask which US distribution hubs are most exposed to weather disruption.
          </p>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6">
          {messages.length === 0 && (
            <div className="grid gap-2 sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => void send(s)}
                  className="rounded-xl border border-slate-200 bg-white p-4 text-left text-sm text-slate-700 shadow-sm transition hover:border-sky-300 hover:shadow"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
              <div
                className={
                  m.role === 'user'
                    ? 'max-w-[80%] rounded-2xl rounded-br-sm bg-sky-600 px-4 py-2 text-white'
                    : 'max-w-[85%] rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-3 shadow-sm'
                }
              >
                {m.steps.length > 0 && (
                  <ul className="mb-2 space-y-1 text-xs text-slate-500">
                    {m.steps.map((step, j) => (
                      <li key={j} className="flex items-center gap-2">
                        <span
                          className={
                            step.done
                              ? 'h-2 w-2 rounded-full bg-emerald-500'
                              : 'h-2 w-2 animate-pulse rounded-full bg-amber-400'
                          }
                        />
                        {step.label}
                      </li>
                    ))}
                  </ul>
                )}
                {m.content ? (
                  <p className={`whitespace-pre-wrap ${m.error ? 'text-rose-600' : ''}`}>{m.content}</p>
                ) : (
                  m.role === 'assistant' && <p className="animate-pulse text-sm text-slate-400">Thinking…</p>
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </main>

      <form onSubmit={onSubmit} className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-3xl items-end gap-2">
          <select
            value=""
            onChange={(e) => insertHub(e.target.value)}
            disabled={hubs.length === 0}
            title={hubsError ? 'Hub list unavailable' : 'Insert a hub into your question'}
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none focus:border-sky-500 disabled:text-slate-400"
          >
            <option value="">{hubsError ? 'Hubs unavailable' : `Hubs (${hubs.length})`}</option>
            {groupByRegion(hubs).map(([region, regionHubs]) => (
              <optgroup key={region} label={region}>
                {regionHubs.map((hub) => (
                  <option key={hub.city} value={hub.city}>
                    {hub.city}, {hub.state_code}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Ask about a hub…"
            className="max-h-40 flex-1 resize-none rounded-xl border border-slate-300 px-4 py-2 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100"
          />
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

export default App
