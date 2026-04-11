---
name: review
description: Invokes the code-review agent on staged/unstaged changes - use when reviewing code changes, checking a diff, or asking for review feedback
---

# Review Skill

Review staged and unstaged changes and provide focused, actionable feedback.

## What It Does

1. Reads the current git diff (staged and unstaged changes)
2. Analyzes the changes for issues
3. Reports findings organized by severity

## Focus Area (Optional)

If the user provides a focus area after `/review`, limit the review to that topic.

Examples:
- `/review` — full review of all changes
- `/review Check for security issues in authentication` — review focused on security in auth code

## Review Checklist

When no focus area is given, check for:

- **Security** — injection risks, hardcoded secrets, missing input validation
- **Correctness** — logic errors, off-by-one errors, unhandled edge cases
- **Error handling** — missing try/except, uncaught exceptions, silent failures
- **Code quality** — unclear naming, overly complex functions, duplicate code
- **Tests** — untested paths, missing assertions, brittle test setup

When a focus area is given, apply the same depth of analysis but scoped to that area only.

## Output Format

```
## Code Review

**Changed files:** [list files from the diff]
**Focus:** [focus area or "General"]

---

### 🔴 Critical
- `file.py:42` — [issue description and suggested fix]

### 🟠 High
- `file.py:15` — [issue description and suggested fix]

### 🟡 Medium
- `file.py:8` — [issue description and suggested fix]

### 🟢 Low / Style
- `file.py:3` — [issue description and suggested fix]

---

**Summary:** [X] issue(s) found. [Brief recommendation: safe to merge / needs fixes before merge]
```

Omit any severity section that has no findings.
