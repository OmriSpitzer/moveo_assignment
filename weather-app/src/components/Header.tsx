/**
 * Header component
 * 
 * @description Displays the header of the app
 */
export const Header = () => {
  return (
    <header className="border-b border-slate-200 bg-white px-6 py-4">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-lg font-semibold text-slate-900">Weather Risk Agent</h1>
        <p className="text-sm text-slate-500">
          Compare your hubs before the next storm.
        </p>
      </div>
    </header>
  )
}
