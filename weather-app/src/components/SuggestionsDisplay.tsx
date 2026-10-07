import type { Hub } from '../types'

/**
 * Suggestions display component
 *
 * @description Displays the suggestion buttons when the chat is empty
 */

// Suggestions for the chat display, built from the loaded hubs
const friendlySuggestions = (hubs: Hub[]): string[] => {
  if (hubs.length === 0) return []
  const regions = new Map<string, Hub[]>()
  for (const hub of hubs) regions.set(hub.region, [...(regions.get(hub.region) ?? []), hub])
  const winter = regions.get('Midwest') ?? regions.get('Northeast') ?? hubs
  const storms = regions.get('South') ?? hubs
  const left = storms[0]
  const right = storms[1] ?? hubs.find((hub) => hub.city !== left.city)
  const snow = winter[0]

  const questions = ['Which hubs do we have in each region?']
  questions.push(
    winter.length > 1
      ? `Which ${winter[0].region} hubs could a hard winter slow down?`
      : `Could a hard winter slow down ${snow.city}?`,
  )
  if (right) questions.push(`How do ${left.city} and ${right.city} compare for storms and floods?`)
  questions.push(`How many days did it snow in ${snow.city} last year?`)
  questions.push(
    storms.length > 1
      ? `Which ${storms[0].region} hubs have had the most disasters since 2000?`
      : `How many disasters has ${left.city} had since 2000?`,
  )
  questions.push(`Does ${hubs[0].city} have any weather alerts right now?`)
  return questions
}

/**
 * Suggestions display component
 * 
 * @description Displays the suggestion buttons when the chat is empty
 */
export const SuggestionsDisplay = ({
  hubs,
  onSuggest,
}: {
  hubs: Hub[]
  onSuggest: (text: string) => void
}) => {
  const suggestions = friendlySuggestions(hubs)
  if (suggestions.length === 0) return null
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {suggestions.map((s) => (
        <button
          key={s}
          type="button"
          onClick={() => void onSuggest(s)}
          className="rounded-xl border border-slate-200 bg-white p-4 text-left text-sm text-slate-700 shadow-sm transition hover:border-sky-300 hover:shadow"
        >
          {s}
        </button>
      ))}
    </div>
  )
}
