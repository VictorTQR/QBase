# AGENTS.md - QBase AI Agent Development Guide

This document provides guidelines for AI coding agents working in the QBase repository.

## Project Overview

QBase is a local knowledge base management system built with Vue 3 + Electron + FastAPI.

**Current Version**: v1.0

**Key Features**:
- Workspace management (add/remove folders)
- File tree navigation (manual refresh support)
- Markdown preview (XMarkdown with syntax highlighting, LaTeX, Mermaid)
- PDF viewer (page navigation, zoom)
- Media player (MP3, MP4, WebM)
- Three-column layout
- Electron file system API
- AI assistant chat panel
- LLM configuration management
- Streaming AI responses (SSE)
- Multi-turn conversation context
- Multi-session management with persistence
- Full-text search with content snippets
- Vector search (LanceDB backend)
- Hybrid search (full-text + vector)
- Smart flashcard generation
- AI generation panel (flashcards, mind maps, summaries)
- Document parse management
- FastAPI backend integration
- MinerU document parsing
- Pinia state persistence with Repository pattern

## Development Principles

### Code Quality Principles
- **Occam's Razor**: Prefer simple solutions
- **KISS**: Keep it simple, stupid
- **YAGNI**: You aren't gonna need it - avoid over-engineering

### Language Preference
- Write documentation in Chinese
- Use Chinese comments
- Commit messages in Chinese

### Testing & QA
- Provide test steps only - DO NOT run tests automatically
- Provide installation commands only - DO NOT execute them automatically

## Package Manager & Commands

Use **npm** as package manager. Work from the `app/` directory.

```bash
cd app                    # Always work from app directory
npm install               # Install dependencies
npm run dev               # Start Vite dev server
npm run build             # Production build
npm run test:unit         # Run all Vitest tests
npm run lint              # Run ESLint + Oxlint with auto-fix
npm run lint:oxlint       # Run Oxlint only
npm run lint:eslint       # Run ESLint only
npm run format            # Prettier format code
npm run ele               # Start Electron
npm run start             # Start Vite + Electron together
npm run pack              # Build + electron-builder --dir
npm run dist              # Build + electron-builder
```

### Running Individual Tests

```bash
npm run test:unit -- src/__tests__/your-test.spec.js
npm run test:unit -- --watch          # Watch mode
npm run test:unit -- --run            # Run once without watch
npm run test:unit -- --reporter dot   # Minimal output
```

## Code Style Guidelines

### Formatting Rules (from .prettierrc.json)
- **No semicolons** (`semi: false`)
- **Single quotes** (`singleQuote: true`)
- **100 character line length** (`printWidth: 100`)
- **2-space indentation**
- **Trailing commas** in multi-line structures

### Import Guidelines
- Use ES module syntax (`import`/`export`)
- Path alias `@` maps to `./src`
- Import grouping: External libraries → Internal modules → Components/styles
- Remove unused imports automatically

### Vue Components
- Use `<script setup>` Composition API syntax
- Use `<style scoped>` for component-scoped styles
- Component filenames in PascalCase (e.g., `MyComponent.vue`)
- Define props and emits with TypeScript or JSDoc

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Variables/Functions | camelCase | `loadFile`, `searchResults` |
| Components | PascalCase | `MarkdownViewer.vue` |
| Constants | UPPER_SNAKE_CASE | `API_BASE_URL`, `MAX_RESULTS` |
| Pinia stores | useXxxStore | `useWorkspaceStore`, `useSearchStore` |
| Test files | *.spec.js | `App.spec.js`, `SearchPanel.spec.js` |

### Error Handling
- Use try/catch for async operations
- Provide meaningful Chinese error messages
- Validate inputs and boundary conditions
- Store errors in reactive state for UI display

## Linting & Testing Tools

**ESLint** (`eslint.config.js`):
- Flat config format
- Vue plugin enabled
- Vitest plugin for test files
- Integrates with Oxlint
- Prettier compatibility (skip formatting rules)

**Oxlint** (`.oxlintrc.json`):
- Fast correctness checks
- Runs before ESLint
- Auto-fix enabled

**Prettier** (`.prettierrc.json`):
- Code formatting
- Runs after linting

**Vitest**:
- Testing framework
- jsdom environment
- `@vue/test-utils` for component testing
- Tests in `src/__tests__/` directory

## Key Configuration Files

All application files live in the `app/` directory:

- `app/package.json` - Dependencies and scripts
- `app/eslint.config.js` - ESLint flat config
- `app/vitest.config.js` - Vitest configuration
- `app/.prettierrc.json` - Prettier rules
- `app/.oxlintrc.json` - Oxlint configuration
- `app/vite.config.js` - Vite configuration

## Project Structure

```
QBase/
├── app/                          # Frontend/Electron app
│   ├── src/
│   │   ├── api/                 # API clients
│   │   ├── components/          # Vue components
│   │   ├── stores/              # Pinia stores
│   │   ├── utils/               # Utilities
│   │   ├── views/               # Page components
│   │   └── __tests__/           # Vitest tests
│   ├── electron/                # Electron main process
│   └── package.json
├── backend/                      # FastAPI backend (Python)
├── docs/                         # Project documentation
│   ├── architecture/             # Architecture docs
│   ├── features/                 # Feature docs
│   ├── implementation/           # Implementation reports
│   └── bugs/                     # Bug records
├── AGENTS.md                     # This file
└── CLAUDE.md                     # Development principles
```

## Documentation Maintenance

### Documentation Directory

```
docs/
├── README.md               # Documentation entry point
├── architecture/           # Architecture design (stable)
├── features/               # Feature implementation (dynamic)
├── implementation/         # Implementation reports (project)
├── bugs/                   # Bug records (project)
└── roadmap.md              # Project roadmap
```

### When to Update Docs

1. **Feature complete**: Update corresponding feature doc status
2. **Milestone complete**: Update roadmap.md and README.md
3. **Major changes**: Create implementation report
4. **Bug fixed**: Create bug record

### Documentation Naming

```
features/<feature-name>.md           # Feature docs
implementation/<version>-complete.md # Implementation reports
bugs/<date>-<bug-name>.md            # Bug records
```

### Status Tags

- ✅ Completed
- 🔄 In Progress
- 📋 Planned
- ⏳ On Hold

## Development Workflow

1. `cd app` - Always work from app directory
2. `npm install` - Install dependencies if needed
3. `npm run dev` - Start Vite dev server
4. `npm run start` - Start full Electron app
5. Before commit: `npm run lint` and `npm run format`
6. Verify tests: `npm run test:unit`

## Git Guidelines

- **Atomic commits**: One feature/fix per commit
- **Commit messages in Chinese**: Use conventional commits
- **Branch from main**: Create feature branches
- **No direct commits to main**: Use PRs when possible

**Commit message format**:
```
<type>: <description in Chinese>

<body if needed>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Related Documents

- [CLAUDE.md](./CLAUDE.md) - Development principles
- [docs/README.md](./docs/README.md) - Documentation entry
- [docs/architecture/tech-stack.md](./docs/architecture/tech-stack.md) - Tech stack details
- [app/package.json](./app/package.json) - Scripts and dependencies

## Cursor/Copilot Rules

No `.cursorrules` or `.github/copilot-instructions.md` found. Follow this AGENTS.md as the primary guide.

