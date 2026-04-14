---
name: explain-code
description: Explain code in plain English for beginners - use when explaining code, understanding what code does, or learning how code works
---

# Explain Code Skill

Break down code into plain, beginner-friendly explanations.

## When This Skill Activates

This skill loads when you ask "explain this code", "what does this do", or "how does this work".

## Explanation Style

- Use everyday analogies (e.g., "a dictionary is like a phone book")
- Define technical terms on first use
- Walk through the code step by step
- Highlight the **why**, not just the **what**
- Keep sentences short and jargon-free

## Output Format

Structure every explanation like this:

```
## Explanation: [function or file name]

### In Plain English
[1-2 sentence summary a non-programmer could understand]

### Step by Step
1. [First thing the code does — with analogy if helpful]
2. [Next step]
...

### Key Concepts
- **[Term]**: [Beginner-friendly definition]

### Try Changing
[Suggest a small tweak the learner can make to see how the code behaves differently]
```

## Guidelines

- Never assume the reader knows Python-specific syntax (explain `self`, `@dataclass`, list comprehensions, etc.)
- When explaining a class, start with what it represents in the real world
- When explaining a function, start with its purpose before walking through the body
- Use comments like "this is similar to..." to connect new concepts to familiar ones
