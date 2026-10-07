import type { AgentEvent, HistoryMessage, Hub } from '../types'

/**
 * Chat services with the agent
 */

// Fetch hubs from the server
export async function fetchHubs(): Promise<Hub[]> {
  const response = await fetch('/api/hubs')
  if (!response.ok) throw new Error(`Server responded with ${response.status}`)
  return (await response.json()) as Hub[]
}

// Stream agent response
export async function streamAgent(
  messages: HistoryMessage[], threadId: string, onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  // Send the chat history to the agent
  const response = await fetch('/api/agent/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, thread_id: threadId }),
    signal,
  })
  if (!response.ok || !response.body) {
    throw new Error(`Server responded with ${response.status}`)
  }

  // Stream the agent response
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''

  // Process the agent response
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
