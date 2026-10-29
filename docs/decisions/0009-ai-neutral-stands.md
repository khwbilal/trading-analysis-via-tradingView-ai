# 0009: An AI Neutral stands; the guards never create a trade

**Date:** 2026-10-22 · **Work item:** WL-021 · **Status:** accepted · Amends [0003](0003-guards-decide-the-bias.md)

## Context

`_apply_confluence_guardrail` upgraded a model's Neutral to the confluence bias when |score| was 3.5 or more. An AI "no trade" can carry information the score lacks (news, structure, a level the score does not see), and an upgraded Neutral is a trade nobody actually proposed.

## Decision

Sheryar chose (2026-10-22): the upgrade is removed. The guards may only make a plan more cautious: chop or a soft score forces Neutral, the opposite side of a strong score is flipped, and the reward:risk guard rejects bad levels. A model Neutral is never turned into Buy or Sell. The case where the confluence bias is Neutral with |score| of 2.5 or more keeps the model's Buy or Sell, as before.

## Consequences

- Fewer Buy and Sell plans, and so fewer archived signals, when the model declines a strong setup.
- `DESK OVERRIDE` now appears only when a guard made the plan more cautious or flipped it.
- Tests in `backend/tests/test_guards.py` pin a Neutral staying Neutral at |score| 3.5 and 4.
