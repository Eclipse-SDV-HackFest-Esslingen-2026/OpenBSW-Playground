---
name: error-patterns
description: "Error Patterns & Solutions documentation skill. Use when: debugging, root cause analysis, troubleshooting, investigating failures, diagnosing errors, fixing bugs, analyzing crashes, error investigation, post-mortem, incident analysis, failure mode analysis, problem resolution, integration issues, runtime errors, protocol errors, communication failures."
argument-hint: "Describe the error or problem you are investigating"
---

# Error Patterns & Solutions Skill

Whenever you **analyze, debug, or resolve an error**, document the finding as a
structured entry in the project's **Error Patterns & Solutions** knowledge base.

This ensures hard-won debugging knowledge is captured, searchable, and
reusable — not buried in commit messages or chat logs.

---

## First-Use Setup

On **first invocation** in a project that does not yet have an error-patterns
file, **ask the user**:

> Where should the **Error Patterns & Solutions** knowledge base be stored?
>
> Suggested locations:
> - `doc/error-patterns.md` (documentation folder)
> - `docs/error-patterns.md` (alternative docs folder)
> - `.github/error-patterns.md` (repo metadata)
> - Custom path

Create the file at the chosen location with this header:

```markdown
# Error Patterns & Solutions

Structured record of errors encountered, their root causes, and solutions.
Each entry follows a consistent template for searchability and reuse.

<!-- STATUS values: RESOLVED | MITIGATED | KNOWN | COSMETIC -->

---
```

If the file already exists, append new entries to it.

---

## Entry Template

Every error entry **must** contain exactly these sections, in this order:

```markdown
### X.Y ERR-<N>: <Short Title> (<STATUS>)

**Root cause**: <One-paragraph technical explanation of WHY the error occurs.
Reference specific functions, modules, protocols, or configuration values.>

**Impact**: <Observable symptoms. What breaks, what the user/system sees.
Include log messages or error codes when available.>

*Requirement: [<requirement-id>]* <!-- omit if no requirements exist -->

\`\`\`
  <ASCII sequence/flow diagram showing the error scenario>
  <Use box-drawing characters and arrows to illustrate the failure point>
\`\`\`

**Solution**:

\`\`\`
  ┌─────────────────────────────────────────────────────────┐
  │  <COMPONENT> FIX: <file or config changed>              │
  │                                                         │
  │  <Concise description of the fix>                       │
  │  <Include code snippets, config values, or commands>    │
  └─────────────────────────────────────────────────────────┘
\`\`\`
```

### STATUS Values

| Status | Meaning |
|:---|:---|
| `RESOLVED` | Fix applied and verified |
| `MITIGATED` | Workaround in place, not a full fix |
| `KNOWN` | Understood but not yet fixed |
| `COSMETIC` | Does not affect functionality |

---

## Rules

1. **Always search** the existing error-patterns file before adding a new entry.
   If the error is already documented, update it instead of duplicating.

2. **Assign sequential IDs** (`ERR-1`, `ERR-2`, …). Continue from the highest
   existing ID in the file.

3. **Root cause must be technical** — name the specific function, module,
   protocol message, or configuration key responsible.

4. **Impact must be observable** — describe what the user or system sees, not
   internal implementation details.

5. **Diagrams are mandatory** for protocol/communication errors and
   multi-component interactions. Use ASCII art with box-drawing characters.
   For simple single-component errors, a diagram is optional.

6. **Solution must be actionable** — include file paths, code snippets,
   configuration changes, or shell commands. Someone reading the entry should
   be able to reproduce the fix.

7. **Link requirements** if the project uses a requirements document or issue
   tracker. Use the project's existing reference format.

8. **Update status** when a KNOWN or MITIGATED error gets fully resolved.

---

## Workflow

```
  Problem reported / observed
           │
           ▼
  ┌─────────────────────┐
  │  1. Reproduce        │  Confirm the error is real
  └────────┬────────────┘
           ▼
  ┌─────────────────────┐
  │  2. Root-cause       │  Trace to the exact code/config
  └────────┬────────────┘
           ▼
  ┌─────────────────────┐
  │  3. Document         │  Write ERR-N entry in error-patterns.md
  │     (even before     │  STATUS = KNOWN
  │      fixing)         │
  └────────┬────────────┘
           ▼
  ┌─────────────────────┐
  │  4. Fix / mitigate   │  Implement the solution
  └────────┬────────────┘
           ▼
  ┌─────────────────────┐
  │  5. Verify           │  Confirm fix works
  └────────┬────────────┘
           ▼
  ┌─────────────────────┐
  │  6. Update entry     │  STATUS → RESOLVED / MITIGATED
  │     Add solution     │  Fill in the Solution section
  └─────────────────────┘
```

 

## Integration with Other Tools

- **Copilot / Cursor / Claude**: This skill triggers automatically when the AI
  detects debugging, error analysis, or troubleshooting activity.
- **Git commits**: Reference `ERR-<N>` in commit messages for traceability.
- **Issue trackers**: Link `ERR-<N>` entries to GitHub Issues or Jira tickets.
- **Requirements docs**: Use `*Requirement: [ID]*` to cross-reference.
