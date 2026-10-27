# 0009: User chooses guard enforce vs AI-only on analyze

**Date:** 2026-10-24 · **Status:** accepted · **Related:** [0003](0003-guards-decide-the-bias.md), WL-063

## Context

Decision 0003 made deterministic guards the final bias after the model replies. Sheryar still wants to judge the AI plan (bias, stop, target) without desk overrides, and to keep the safe default for archived signals.

## Decision

`POST /api/analyze` accepts `guard_mode`:

- `enforce` (default): same as 0003 (confluence / pack quality, traps, R:R may change bias; `DESK OVERRIDE:` when desk pipeline bias flips).
- `ai_only`: keep the model bias and levels; still fill blank prices from the snapshot; prompt treats confluence MUST lines as advisory for that run. No post-AI bias flip.

Desk shows a **Guards** select before Full analysis. The response echoes `guard_mode`; `market.guard_mode` is stored with the snapshot when a signal is archived.

## Consequences

- Default behaviour and signal archive safety stay on enforce.
- AI-only runs can archive Buy/Sell that enforce would have forced Neutral; compare modes when reading hit rates.
- 0003 remains the default path; this note adds an opt-out, it does not replace 0003.
- **Exception (WL-081):** a live mark already through the printed stop always forces Neutral, even under `ai_only`. That is market invalidation of the levels, not confluence taste.
