## Problem
Add a new `mark-read` command to the book app CLI so users can mark an existing book as read.

## Current state (analysis)
- `samples/book-app-project/books.py` already supports this behavior with `BookCollection.mark_as_read(title) -> bool`.
- `samples/book-app-project/book_app.py` currently exposes commands: `list`, `add`, `remove`, `find`, and `help`.
- The CLI does not yet expose a command that calls `mark_as_read`.
- Existing tests focus on `books.py`; there are no direct tests for `book_app.py` command handlers.

## Confirmed decisions
- Command name: `mark-read`
- Title input style: prompt the user with `input()` at runtime

## Scope and boundaries
### In scope
- Add a new CLI handler in `book_app.py` for `mark-read`.
- Wire `mark-read` into command routing and help text.
- Provide user feedback for both success and not-found outcomes.
- Add targeted tests for the new CLI command behavior.

### Out of scope
- Refactoring unrelated commands.
- Changing storage/data model behavior in `books.py`.

## Implementation approach
1. **Add handler**
   - Create `handle_mark_read()` in `book_app.py`.
   - Prompt for title using `input(...).strip()`.
   - Call `collection.mark_as_read(title)` and branch on returned boolean.
2. **Wire command**
   - Add `mark-read` to `show_help()` command list.
   - Add a dispatch branch in `main()` for `mark-read`.
3. **User feedback**
   - If book found: print confirmation message.
   - If not found: print a clear “book not found” message.
4. **Testing**
   - Add tests for the new handler/dispatch path using monkeypatching for `input` and captured output.
   - Cover success and failure cases.
5. **Verification**
   - Run the sample pytest suite and ensure all tests pass.

## Deliverables
- Updated `book_app.py` with `mark-read` command support.
- Updated help output listing `mark-read`.
- Tests validating command behavior.

## Todos
1. **add-mark-read-handler**  
   Implement `handle_mark_read()` using prompted title input and boolean result handling.
2. **wire-mark-read-command**  
   Add `mark-read` to help text and `main()` command dispatch.
3. **add-mark-read-tests**  
   Add pytest coverage for success and not-found CLI command scenarios.
4. **verify-mark-read-flow**  
   Run tests to confirm the command works and no regressions were introduced.

## Notes
- Keep changes beginner-friendly and consistent with existing CLI style.
- Do not implement additional command aliases unless explicitly requested.
