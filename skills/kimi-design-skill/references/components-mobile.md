# Components Mobile

This file defines Kimi mobile component rules for AI-generated UI. Read it after `principles.md` and `tokens.json` when the target platform is Mobile.

Status: draft reference. Mobile does not yet have production component specs or per-component files. Use these rules as platform guidance, not as a complete component contract.

Token mapping status: draft. Use finalized semantic token paths from `tokens.json`; do not invent permanent token names from local component needs. When mobile-specific metrics are missing, record the gap instead of copying Web component metrics mechanically.

## Global Mobile Component Rules

- Use `tokens.json` as the source of truth.
- Mobile components should prioritize touch clarity, vertical rhythm, and thumb-friendly placement.
- Do not rely on hover states.
- Use pressed, disabled, loading, error, and focus/accessibility states where applicable.
- Touch targets should generally be at least `44px` high.
- Do not mechanically shrink Web layouts into Mobile.

## Button

Status: draft placeholder.

### Use When

Use Button for primary, secondary, destructive, or navigation-like touch actions.

### Sizes

- Use `44px` or larger for standard mobile touch actions.
- Use compact sizes only for dense inline contexts where accessibility is still preserved.

### States

- default
- pressed
- disabled
- loading

### Rules

- Use one primary button per local action group.
- Put high-priority actions near the active task area or bottom action region.
- Do not rely on hover behavior.
- Destructive actions must use danger semantics, not arbitrary emphasis.

## Input

Status: TODO.

## List Item

Status: TODO.

## Navigation Bar

Status: TODO.

## Bottom Sheet

Status: TODO.

## Toast

Status: TODO.

## Empty State

Status: TODO.
