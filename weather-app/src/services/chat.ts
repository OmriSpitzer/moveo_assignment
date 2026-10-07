import type { AgentEvent, ChatMessage } from '../types'

/**
 * Chat services
 */

// Tool labels
const TOOL_LABELS: Record<string, string> = {
  list_hubs: 'Reading the hub list',
  score_hubs: 'Scoring hub risk',
  get_location: 'Finding the hub location',
  get_weather_history: 'Reading weather history',
  get_disaster_history: 'Reading disaster history',
  get_active_alerts: 'Checking active alerts',
  get_current_weather: 'Checking current weather',
}

// Get place names
const placeNames = (value: unknown): string | null => {
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

// Get step label
const stepLabel = (name: string, args: Record<string, unknown>): string => {
  const label = TOOL_LABELS[name] ?? name
  const places = placeNames(args.places) ?? placeNames(args.points) ?? placeNames(args.cities)
  if (places) return `${label} for ${places}`
  return typeof args.city === 'string' ? `${label}: ${args.city}` : label
}

// Apply event to message
export const applyEvent = (message: ChatMessage, event: AgentEvent): ChatMessage => {
  switch (event.type) {
    // Tool call event
    case 'tool_call':
      return {
        ...message,
        steps: [...message.steps, { id: event.id, label: stepLabel(event.name, event.args), done: false }],
      }

    // Tool result event
    case 'tool_result':
      return { ...message, steps: message.steps.map((s) => (s.id === event.id ? { ...s, done: true } : s)) }
    
    // Answer event
    case 'answer':
      return { ...message, content: event.answer.answer }

    // Error event
    case 'error':
      return { ...message, content: event.message, error: true }
    default:
      return message
  }
}