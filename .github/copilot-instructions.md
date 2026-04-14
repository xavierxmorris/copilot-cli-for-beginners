# Copilot Instructions

This repo is a **beginner-friendly course** teaching GitHub Copilot CLI. The primary deliverable is markdown chapters and demo GIFs — not the Python sample apps. Treat it as educational content, not a software project.

## Build & Test

```bash
# Course materials (generates chapter headers + demo GIFs)
npm install && npm run release

# Sample app tests
python -m pytest samples/book-app-project/tests -q

# Single test
python -m pytest samples/book-app-project/tests/test_books.py::test_add_book -q
```

## Sample Code Is Teaching Material

All code under `samples/` exists to illustrate concepts across the 8 course chapters. Treat these files as **read-only** unless the user explicitly requests a change and understands it affects course content.

- `samples/book-app-project/` — Primary Python sample used in every chapter. Do not refactor, add validation, improve error handling, or "harden" this code unprompted.
- `samples/book-app-buggy/` and `samples/buggy-code/` — **Intentionally broken** for debugging exercises. Never fix these.
- `samples/book-app-project-cs/` and `samples/book-app-project-js/` — C# and JS translations of the primary sample.

### When reviewing sample code

Missing input validation, simplified error handling, bare `dict` returns, and absent edge-case tests are **deliberate pedagogical choices** — not bugs. Focus reviews on actual logic errors or crashes, not production-hardening suggestions. Do not repeatedly flag the same known simplifications across sessions.

## Conventions

- Keep explanations beginner-friendly; define AI/ML jargon on first use
- Use `samples/book-app-project/` paths in all primary examples
- Use Python/pytest context for code examples
- Tone: friendly, encouraging, practical
- Never create planning, scratch, or temporary files in the repo working tree — use the session workspace only
- When adding chapters, update the course table in `README.md`
