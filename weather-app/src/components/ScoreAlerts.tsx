import { useEffect, useRef } from 'react'
import type { ScoreAlert } from '../types'

/**
 * Score alerts beside the chat
 *
 * @description Yellow notices for a hub score that changed. The list scrolls on its own.
 */
export const ScoreAlerts = ({ alerts }: { alerts: ScoreAlert[] }) => {
  const listRef = useRef<HTMLDivElement>(null)

  // Scroll this list only, so the chat position stays put.
  useEffect(() => {
    const list = listRef.current
    if (list) list.scrollTop = list.scrollHeight
  }, [alerts])

  if (alerts.length === 0) return null

  return (
    <aside
      ref={listRef}
      aria-label="Score alerts"
      className="pointer-events-auto absolute inset-y-0 right-3 w-64 overflow-y-auto py-4"
    >
      <div className="flex flex-col gap-2">
        {alerts.map((alert) => (
          <p key={alert.id} className="rounded-xl bg-yellow-200 px-3 py-2 text-sm text-yellow-950">
            {alert.city} score changed from {alert.previous} to {alert.score}
          </p>
        ))}
      </div>
    </aside>
  )
}
