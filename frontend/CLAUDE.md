# Frontend Development Guide (CLAUDE.md)

This file defines the development commands and code conventions specifically for the Next.js frontend application. For the project-wide developer and backend guidelines, refer to the root [CLAUDE.md](../CLAUDE.md).

## Development Commands

- **Install dependencies**: `npm install`
- **Run local development server**: `npm run dev`
- **Build production app**: `npm run build`
- **Run lint checks**: `npm run lint`
- **Run Vitest suite (interactive watch)**: `npm run test`
- **Run Vitest suite (single run)**: `npm run test:run`

## Code Conventions & Guidelines

### TypeScript & Types
- **Strict Typing**: Do not use `any`. Always define interfaces and type definitions for API payloads.
- **Contract Synchronization**: Ensure data types under `frontend/lib/` or custom hooks match the FastAPI model responses (`src/apr_twin/schemas.py`).
- **File Extensions**: Use `.ts` for business logic, formats, and API helpers. Use `.tsx` for React components.

### React Components (Next.js & React 19)
- **Component Style**: Functional components with TypeScript props typing.
- **Client vs Server**: By default, Next.js components are server components. Add `"use client"` at the top of files that require browser hooks (`useState`, `useEffect`, SWR, event handlers).
- **Structure**: Reusable UI primitives in `components/ui/`, feature/page components in `components/`.

### Styling (Tailwind CSS v4)
- Use Tailwind CSS v4 styling rules.
- Leverage HSL tailored palettes and modern variables for glassmorphism, responsive grid layouts, card borders, shadows, and clean interactive elements.

### Testing (Vitest & JSDOM)
- All test files must reside under `tests/` or end in `.test.ts` / `.test.tsx`.
- Use `@testing-library/react` and `@testing-library/jest-dom` for rendering and DOM assertion.
