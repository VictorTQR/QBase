# AGENTS.md - AI Agent Guidelines for QBase

This document provides instructions for AI coding agents working on the QBase repository.

## Project Overview

QBase is a Vue 3 + Electron desktop application built with:

- Vue 3 (Composition API with `<script setup>`)
- Pinia for state management
- Vue Router for routing
- Electron for desktop packaging
- Vite as the build system
- Vitest for testing

## Package Manager & Commands

**npm** is the package manager. Key commands:

```bash
npm install          # Install dependencies
npm run dev          # Start Vite dev server
npm run build        # Build for production
npm run test:unit    # Run all Vitest tests
npm run lint         # Run ESLint + Oxlint with auto-fix
npm run format       # Format code with Prettier
npm run ele          # Start Electron
npm run start        # Concurrent Vite + Electron
```

### Running Single Tests

To run a single test file:

```bash
npm run test:unit -- src/__tests__/your-test.spec.js
```

To run tests in watch mode:

```bash
npm run test:unit -- --watch
```

## Code Style Guidelines

### General Principles (from CLAUDE.md)

- **Occam's Razor**: Prefer simple solutions
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Ain't Gonna Need It - avoid over-engineering
- **Chinese language**: Use Chinese for all comments, documentation, and commit messages

### Formatting Rules

- No semicolons
- Single quotes for strings
- 100-character line length
- 2-space indentation
- Trailing commas in multi-line structures

### Imports

- ES module syntax (`import`/`export`)
- Path alias `@` maps to `./src`
- Group imports: external → internal → components/styles
- No unused imports

### Vue Components

- Use `<script setup>` syntax
- Scoped styles with `<style scoped>`
- Component filenames: PascalCase (e.g., `MyComponent.vue`)
- Props and emits defined with TypeScript or JSDoc

### Naming Conventions

- Variables & functions: camelCase
- Components: PascalCase
- Constants: UPPER_SNAKE_CASE
- Pinia stores: useXxxStore
- Test files: `*.spec.js` in `__tests__` directories

### Error Handling

- Use try/catch for async operations
- Provide meaningful error messages in Chinese
- Validate inputs and edge cases

## Linting & Testing Stack

- **ESLint**: Flat config with Vue and Vitest plugins (`eslint.config.js`)
- **Oxlint**: Fast correctness linter (`.oxlintrc.json`)
- **Prettier**: Code formatting (`.prettierrc.json`)
- **Vitest**: Testing framework with jsdom and `@vue/test-utils`

## Key Configuration Files

- `package.json` - Dependencies and scripts
- `eslint.config.js` - ESLint configuration
- `vitest.config.js` - Vitest configuration
- `.prettierrc.json` - Prettier rules
- `.oxlintrc.json` - Oxlint configuration
- `../CLAUDE.md` - Project guidelines (Chinese)

## Development Workflow

1. Run `npm install` for dependencies
2. `npm run dev` for Vite dev server
3. `npm run start` for full Electron app
4. `npm run lint` and `npm run format` before commits
5. `npm run test:unit` to verify tests pass

## Agent/Cursor/Copilot Rules

No existing Cursor or Copilot rule files found. Follow:

- Guidelines in this AGENTS.md
- Principles in CLAUDE.md
- Existing code patterns in the codebase
