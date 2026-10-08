/**
 * Types for the weather app
 */

// Role types
export type Role = 'user' | 'assistant'

// History message type
export type HistoryMessage = { role: Role; content: string }

// Hub type
export type Hub = { city: string; state_code: string; region: string }

// Answer type
export type Answer = {
  timestamp: string
  model: string
  prompt: string
  answer: string
}

// Agent event type
export type AgentEvent =
  | { type: 'tool_call'; id: string; name: string; args: Record<string, unknown> }
  | { type: 'tool_result'; id: string; name: string; content: string }
  | { type: 'score_alert'; city: string; previous: number; score: number }
  | { type: 'answer'; answer: Answer }
  | { type: 'error'; message: string }
  | { type: 'done' }

// Score change shown beside the chat
export type ScoreAlert = { id: string; city: string; previous: number; score: number }

export const ALERT_MS = 8000

// Step type
export type Step = { id: string; label: string; done: boolean }

// Chat message type
export type ChatMessage = {
  role: Role
  content: string
  steps: Step[]
  error?: boolean
}
