# Frontend

## Overview

A React 18 SPA built with TypeScript, Vite, Tailwind CSS, and Shadcn UI.
All data fetching goes through TanStack Query. Client-only state lives in Zustand stores.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| React 18 | UI framework |
| TypeScript 5 (strict) | Type safety |
| Vite | Build tool and dev server |
| Tailwind CSS | Utility-first styling |
| Shadcn UI | Pre-built accessible components |
| TanStack Query v5 | Server state — all API calls |
| Zustand v4 | Client state — auth, theme, filters |
| React Router v6 | Client-side routing |

---

## Project Structure

```
frontend/src/
├── main.tsx                App entry point
├── App.tsx                 Router setup, layout wrapping
├── components/
│   ├── ui/                 Shadcn UI primitives (auto-generated)
│   ├── JobCard.tsx         Job offer card (used in search + saved)
│   ├── MatchScore.tsx      Visual score ring for recommendations
│   ├── SkillBadge.tsx      Colored skill pill (matched / missing / neutral)
│   ├── FilterPanel.tsx     Contract type + location filter sidebar
│   ├── SearchBar.tsx       Debounced search input
│   ├── Pagination.tsx      Page navigation
│   ├── PageSkeleton.tsx    Loading state skeleton
│   ├── EmptyState.tsx      Empty result state
│   ├── ErrorBoundary.tsx   Route-level error fallback
│   ├── ProtectedRoute.tsx  Redirects to /login if not authenticated
│   └── AdminRoute.tsx      Restricts to admin role
├── pages/
│   ├── Login.tsx           JWT login form
│   ├── Register.tsx        Account creation form
│   ├── Dashboard.tsx       Stats overview (animated counters, charts)
│   ├── JobSearch.tsx       Full-text and filtered job listing
│   ├── JobDetail.tsx       Single job detail + save/unsave
│   ├── Recommendations.tsx AI-matched job cards with score breakdown
│   ├── SkillGap.tsx        Missing skills ranked by market frequency
│   ├── Profile.tsx         Candidate profile form (create + update)
│   ├── SavedJobs.tsx       Bookmarked job offers
│   └── admin/              Admin-only views
├── hooks/
│   ├── useAuth.ts          Login, logout, register mutations
│   ├── useJobs.ts          Job list query with filter params
│   ├── useRecommendations.ts  Recommendation query + cache
│   ├── useSemanticSearch.ts   Semantic search query
│   ├── useSkillGap.ts      Skill gap query
│   ├── useSavedJobs.ts     Saved jobs list + save/unsave mutations
│   ├── useDebounce.ts      Debounce hook for search input
│   └── useCountUp.ts       Animated number counter (dashboard)
├── services/
│   ├── api-client.ts       Centralized fetch wrapper (token injection, error normalization)
│   ├── auth.service.ts     login(), register(), me()
│   ├── jobs.service.ts     listJobs(), getJob(), saveJob(), unsaveJob()
│   ├── candidates.service.ts  getProfile(), createProfile(), updateProfile()
│   └── recommendations.service.ts  getRecommendations(), getSkillGap(), search()
├── store/
│   ├── auth.store.ts       User identity (token, user object, isAuthenticated)
│   ├── theme.store.ts      dark | light — persisted to localStorage
│   └── filters.store.ts    Active job search filters
├── config/
│   └── routes.tsx          Route definitions
└── types/
    └── index.ts            TypeScript interfaces matching backend schemas
```

---

## Pages

### Dashboard
- Animated stat counters (total jobs, active candidates, matches generated)
- Quick navigation cards to main features
- Supports dark and light mode

### Job Search (`/jobs`)
- Paginated job list with `FilterPanel` (contract type, location)
- Debounced search input
- Each card shows title, company, location, contract type, skills
- Save / unsave directly from the card

### Job Detail (`/jobs/:id`)
- Full job description
- Required skills as `SkillBadge` components
- Save / unsave button

### Recommendations (`/recommendations`)
- Powered by `POST /api/v1/recommendations`
- Each card shows `MatchScore` ring + matched/missing skill badges
- Score breakdown tooltip (skill overlap, embedding, seniority, location)
- Empty state if profile has no skills

### Skill Gap (`/skill-gap`)
- Lists skills the candidate is missing for their target roles
- Ranked by market frequency (high / medium / low priority)
- Coverage score shown as a progress bar

### Profile (`/profile`)
- Form to create or update candidate profile
- Fields: name, title, skills (tag input), experience years, education, location, salary, contract preferences
- Profile completeness percentage indicator
- On save: backend auto-generates/updates candidate embedding

### Saved Jobs (`/saved-jobs`)
- List of bookmarked job offers
- Unsave directly from the list

### Login / Register
- JWT login and account creation forms
- Redirects to dashboard on success
- Token stored in Zustand `auth.store`

---

## State Management

### TanStack Query — Server State
Every API call is a TanStack Query `useQuery` or `useMutation`.

Query key conventions:
```ts
["jobs", filters]                    // job list
["job", jobId]                       // single job
["recommendations", candidateId]     // recommendations
["skill-gap", candidateId]           // skill gap
["saved-jobs", candidateId]          // saved jobs
["profile"]                          // candidate profile
```

Mutations invalidate related queries automatically on success.

### Zustand — Client State

| Store | State |
|---|---|
| `auth.store` | `token`, `user`, `isAuthenticated` — persisted to localStorage |
| `theme.store` | `theme: "dark" \| "light"` — persisted to localStorage |
| `filters.store` | Active job search filters (contract, location) — session only |

---

## Theme System

- Tailwind `dark:` variant for all component styles
- Dark mode class applied to `<html>` element
- `theme.store` persists user preference to `localStorage`
- System preference detected on first load (`prefers-color-scheme`)
- Toggle button in the top navigation bar

---

## API Client

`services/api-client.ts` is a thin wrapper around the Fetch API:
- Injects `Authorization: Bearer <token>` from `auth.store` on every request
- Normalizes error responses to `{ detail, code }` shape
- On 401 → clears auth store (auto-logout)
- Base URL configured via `VITE_API_URL` env variable (default: `http://localhost:8000`)

---

## Environment Variables

```env
VITE_API_URL=http://localhost:8000   # Backend API base URL
```

---

## Running Locally

```bash
cd frontend
npm install
npm run dev       # Starts on http://localhost:5173
```

Production build:
```bash
npm run build     # Output to dist/
```

The frontend is **not** containerized in development — Vite's dev server runs directly on the host and proxies API calls to the Docker FastAPI container.
