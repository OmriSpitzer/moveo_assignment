import type { Hub } from '../types'

// Group hubs by region
const groupByRegion = (hubs: Hub[]): [string, Hub[]][] => {
  const groups = new Map<string, Hub[]>()
  for (const hub of hubs) groups.set(hub.region, [...(groups.get(hub.region) ?? []), hub])
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b))
}

/**
 * Hubs dropdown component
 * 
 * @description Displays a dropdown of hubs with the region and city
 */
export default function HubsDropUp({
  hubs,
  hubsError,
  selected,
  onSelect,
}: {
  hubs: Hub[]
  hubsError: boolean
  selected: string
  onSelect: (city: string) => void
}) {
  const chosen = selected !== ''
  return (
    <select
      value={selected}
      onChange={(e) => onSelect(e.target.value)}
      disabled={hubs.length === 0}
      title={hubsError ? 'Hub list unavailable' : 'Choose a hub'}
      className={`rounded-xl border px-3 py-2 text-sm outline-none focus:border-sky-500 disabled:text-slate-400 ${
        chosen ? 'border-sky-400 bg-sky-50 text-sky-900' : 'border-slate-300 bg-white text-slate-700'
      }`}
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
  )
}
