# Change Request CR-001: Convert ASCII Art Architecture Diagrams to Mermaid

**Date:** 2026-04-29  
**Requested by:** Project Manager  
**Assigned to:** Change Manager  
**Priority:** Medium  
**Mode:** autonomous  
**Status:** In Progress  

---

## Summary

Replace all ASCII/Unicode box-drawing art diagrams in the architecture
documentation with proper Mermaid diagrams. Mermaid is natively rendered by
GitHub, Sphinx (via sphinx-mermaidjs), and most modern documentation toolchains,
providing consistent, scalable, and maintainable diagrams.

---

## Scope

### Affected Files

| File | Diagrams | Type |
|------|---------|------|
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | System Architecture (§1) | `graph LR` / `C4Context` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | Software Stack Layers (§2) | `graph TB` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | CMake Overlay Structure (§3) | `graph TD` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | DoIP Good-Case DID Read (§4.1) | `sequenceDiagram` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | DoIP Fault Memory Read (§4.2) | `sequenceDiagram` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | DoIP Connection Setup (§4.3) | `sequenceDiagram` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | ERR-1 NACK sequence (§5.1) | `sequenceDiagram` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | ERR-1 solution box (§5.1) | `graph TD` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | ERR-2 SIGTTOU sequence (§5.2) | `sequenceDiagram` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | ERR-2 solution box (§5.2) | `graph TD` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | ERR-3 DID mismatch (§5.3) | `sequenceDiagram` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | ERR-4 variant detection (§5.4) | `sequenceDiagram` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | ERR-5 AliveCheck NACK (§5.5) | `sequenceDiagram` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | ERR-6 bridge network (§5.6) | `sequenceDiagram` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | ERR-6 solution box (§5.6) | `graph TD` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | Local deployment mode (§8.1) | `graph TB` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | Docker Compose deployment (§8.2) | `graph TB` |
| `OpenBSW-SOVD-Demo/doc/demo-architecture.md` | Pre-built CDA binary paths (§9) | `graph LR` |
| `OpenBSW-SOVD-Demo/real-sovd-cda/README.md` | Component architecture (§Architecture) | `graph LR` |

---

## Requirements

### Functional Requirements

1. **All ASCII art diagrams must be converted** — No Unicode box-drawing chars
   (┌─┐│└─┘) or ASCII art sequences (→ < ────) may remain as standalone diagrams.
2. **Semantic accuracy** — Each Mermaid diagram must faithfully represent the
   same information as its ASCII art predecessor (no information loss, no change
   in meaning).
3. **Sequence diagrams** — All communication flow diagrams (§4.x and §5.x) must
   use `sequenceDiagram` with proper participant labels, arrows, and notes.
4. **Architecture diagrams** — System/component box diagrams must use
   `graph LR` or `graph TD` with labelled nodes and edges that match the
   original IP addresses, port numbers, and role descriptions.
5. **Mermaid syntax validity** — All generated diagrams must be syntactically
   valid Mermaid. Validate using the Mermaid CLI (`mmdc`) or equivalent.
6. **No content removal** — Surrounding prose, code blocks (C++/TOML), and
   section headings must remain unchanged.

### Implementation Notes

- Use `mermaid` fenced code blocks (` ```mermaid `)
- For the software stack layers (§2): use `graph TB` with subgraphs or
  `flowchart TB` blocks; clearly indicate layer boundaries
- For the CMake overlay file tree (§3): a `graph TD` showing the directory
  structure and build relationships is preferred over raw text tree
- For solution/fix summary boxes (ERR-1, ERR-2, ERR-6): use `graph TD` with
  rectangular nodes for multi-part fix descriptions
- Variant detection ERR-4 and ERR-5 (AliveCheck) are short; keep them as
  `sequenceDiagram` with notes
- The `real-sovd-cda/README.md` diagram has 3 components (ECU, CDA, Grafana)
  with DoIP and REST connections — use `graph LR`

### Validation Requirements

1. Run `mmdc` (Mermaid CLI) on every replaced diagram to confirm valid rendering.  
   Install with: `npm install -g @mermaid-js/mermaid-cli`
2. Verify semantic correctness: check that endpoints, protocols, port numbers,
   IP addresses, and flow directions match the original ASCII art exactly.
3. Commit only after all diagrams render without errors.

---

## Acceptance Criteria

- [ ] All 19 ASCII art diagrams in the two target files are replaced with Mermaid
- [ ] `mmdc` renders every diagram without error
- [ ] IP addresses, port numbers, participants, and arrows match originals
- [ ] No surrounding prose or code blocks are accidentally removed
- [ ] Changes committed to a feature branch (`feature/ascii-art-to-mermaid`)

---

## Out of Scope

- RST files (`.rst`) — these use Sphinx-specific directives; a separate CR is
  needed for those
- Markdown tables — these are already well-structured and do not need conversion
- Code blocks (C++, TOML, shell) — remain as-is

---

## Delegation

- 2026-04-29: PM delegated CR-001 to the Change Manager for autonomous execution.
- 2026-04-29: Scope confirmed to include all standalone ASCII architecture diagrams in `demo-architecture.md` and the component architecture diagram in `real-sovd-cda/README.md`.
- Validation gate: Mermaid rendering must pass before CR-001 can move to Done.

