import { useEffect, useRef } from 'react'
import type { ChatMessage, Hub } from '../types'
import MessageCard from './MessageCard'
import { SuggestionsDisplay } from './SuggestionsDisplay'

/**
 * Chat display component
 * 
 * @description Displays the chat display with the messages and suggestions
 */
export const ChatDisplay = ({
  messages,
  hubs,
  onSuggest,
}: {
  messages: ChatMessage[]
  hubs: Hub[]
  onSuggest: (text: string) => void
}) => {
  // Reference to the bottom of the chat display
  const bottomRef = useRef<HTMLDivElement>(null)

  // Scroll to the bottom of the chat display
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <main className="flex-1 overflow-y-auto">
      {/* Chat display */}
      <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6">
        {messages.length === 0 && <SuggestionsDisplay hubs={hubs} onSuggest={onSuggest} />}

        {/* Messages */}
        {messages.map((message, i) => (
          <MessageCard key={i} message={message} />
        ))}

        {/* Bottom reference */}
        <div ref={bottomRef} />
      </div>
    </main>
  )
}
