export type Role = 'user' | 'assistant'

export type HistoryMessage = { role: Role; content: string }

export type Hub = { city: string; state_code: string; region: string }

export async function fetchHubs(): Promise<Hub[]> {
  const response = await fetch('/api/hubs')
  if (!response.ok) throw new Error(`Server responded with ${response.status}`)
  return (await response.json()) as Hub[]
}

export type Answer = {
  timestamp: string
  model: string
  prompt: string
  answer: string
}

export type AgentEvent =
  | { type: 'tool_call'; id: string; name: string; args: Record<string, unknown> }
  | { type: 'tool_result'; id: string; name: string; content: string }
  | { type: 'answer'; answer: Answer }
  | { type: 'error'; message: string }
  | { type: 'done' }

export async function streamAgent(
  messages: HistoryMessage[],
  threadId: string,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch('/api/agent/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, thread_id: threadId }),
    signal,
  })
  if (!response.ok || !response.body) {
    throw new Error(`Server responded with ${response.status}`)
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += value
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''
    for (const frame of frames) {
      const data = frame
        .split('\n')
        .find((line) => line.startsWith('data: '))
      if (data) onEvent(JSON.parse(data.slice('data: '.length)) as AgentEvent)
    }
  }
}
