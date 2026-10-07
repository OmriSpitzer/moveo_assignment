import type { ChatMessage } from '../types'

/**
 * Message card component
 * 
 * @description Displays a message card with the message content and role
 */
export default function MessageCard({ message }: { message: ChatMessage }) {
    // Flag for active step
  const active = message.content || message.error ? null : message.steps.find((step) => !step.done)
  
  return (
    <div className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
      <div
        className={
          message.role === 'user'
            ? 'max-w-[80%] rounded-2xl rounded-br-sm bg-sky-600 px-4 py-2 text-white'
            : 'max-w-[85%] rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-3 shadow-sm'
        }
      >
        {active && (
          <p className="mb-2 flex items-center gap-2 text-xs text-slate-500">
            <span className="h-2 w-2 animate-pulse rounded-full bg-amber-400" />
            {active.label}
          </p>
        )}
        {message.content ? (
          <p className={`whitespace-pre-wrap ${message.error ? 'text-rose-600' : ''}`}>{message.content}</p>
        ) : (
          message.role === 'assistant' && <p className="animate-pulse text-sm text-slate-400">Thinking…</p>
        )}
      </div>
    </div>
  )
}
