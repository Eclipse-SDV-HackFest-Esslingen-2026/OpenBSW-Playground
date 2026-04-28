---
marp: true
theme: default
paginate: false
---

# Error Patterns & Solutions Process

```
 Reproduce → Root-cause → Document → Fix → Verify → Update
```

---

<!--
_class: lead
-->

## Entry Structure

| Section | Content |
|:---|:---|
| **ERR-N: Title (STATUS)** | Sequential ID + state |
| **Root cause** | *Which* function / config / protocol failed and *why* |
| **Impact** | What the user or system observes |
| **Diagram** | ASCII flow showing the failure point |
| **Solution** | File paths, code, config — actionable fix |

**STATUS**: `RESOLVED` · `MITIGATED` · `KNOWN` · `COSMETIC`

---

## AI-Assisted Workflow

```
  ┌──────────────┐   ┌─────────────────┐    ┌───────────────────────┐
  │  Error seen  │──>│ AI & dev analyzes    -│──>│ Entry written to  │
  │  or reported │   │ root cause +    │    │ error-patterns.md     │
  │              │   │ impact          │    │ (asks path on 1st use)│
  └──────────────┘   └─────────────────┘    └───────────────────────┘
```

- Skill auto-triggers on **debugging / troubleshooting** tasks
- First run asks: *"Where to store `error-patterns.md`?"*
- Entries are **searchable**, **linkable** to requirements & commits

