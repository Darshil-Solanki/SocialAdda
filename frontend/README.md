# SocialAdda frontend

Next.js (App Router, TypeScript) client for the SocialAdda API.

## Run locally

Start the Django backend first (see the root README), then:

```
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Next.js forwards `/api/v1/*` and `/media/*` to the backend, so the browser never makes cross-origin requests.

| Variable | Purpose | Default |
|---|---|---|
| `BACKEND_URL` | Django base URL used by the rewrites | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket base URL for live chat | `ws://localhost:8000` |

## Scripts

- `npm run dev`: development server
- `npm run build` / `npm start`: production build and server
- `npm test`: Vitest unit tests
- `npm run typecheck`: TypeScript check
- `npm run lint`: ESLint

## Structure

- `src/app/(app)/`: authenticated pages (feed, following, saved, profile, search, messages, settings). The layout guards the session.
- `src/app/login`, `src/app/signup`: public auth pages
- `src/lib/api.ts`: fetch wrapper with bearer auth and single-flight token refresh
- `src/lib/queries.ts`: TanStack Query hooks, including optimistic like and bookmark toggles
- `src/lib/auth.tsx`: session provider
- `src/components/`: post card, composer, comments, feed, navigation, follow button