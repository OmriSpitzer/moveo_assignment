# how to add tailwind to the react app

- Session: `822729c7-462b-4b56-87bd-2b5b40cac7b6`
- Started: 2026-10-07 12:18

## You

how to add tailwind to the react app

## Agent

The user wants to add Tailwind to their Vite React app, so I should check the package.json and vite config first to tailor the setup steps correctly.

Your app runs on Vite 8, so the simplest route is Tailwind v4 with its official Vite plugin. You don't need a `tailwind.config.js` or PostCSS setup.

**1. Install** (from `web/weather-app`):

```powershell
npm install tailwindcss @tailwindcss/vite
```

**2. Add the plugin to `vite.config.ts`:**

```ts
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] }),
    tailwindcss(),
  ],
})
```

**3. Import Tailwind in `src/index.css`.** Put this line at the top of the file:

```css
@import "tailwindcss";
```

`main.tsx` already imports `index.css`, so nothing else needs to change. The default Vite template styles in `index.css` and `App.css` will clash with Tailwind's base styles. You'll probably want to delete them, and remove the `import './App.css'` line from `App.tsx`.

**4. Check that it works.** Run `npm run dev` and put a class on any element, for example:

```tsx
<h1 className="text-3xl font-bold text-blue-600">Weather Risk</h1>
```

If the text shows up large, bold and blue, Tailwind is working.

**If the install fails:** if npm reports a peer dependency conflict between `@tailwindcss/vite` and Vite 8, update to the latest `@tailwindcss/vite`. If it still fails, install with `--legacy-peer-deps`.

I can make these changes for you if you'd like. Under the project rules, I'd also add a test entry in `docs/tests.md` and a work log entry in `docs/requirements.md`.

I'm thinking about potential version compatibility between the Vite plugin and Tailwind v4, and wondering if I should note a fallback like --legacy-peer-deps in case of peer dependency mismatches, then outline the setup steps.

Tools: `Read`, `Glob`
