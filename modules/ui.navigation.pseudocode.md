# ui.navigation - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "ui.navigation",
  "target_file": "src/ui/navigation.py",
  "language": "python",
  "runtime": {
    "python": "3.11"
  },
  "index_base": 0,
  "newline": "LF",
  "dependencies": [
    "core.contracts"
  ],
  "acceptance": {
    "lint": [
      "ruff check .",
      "ruff format --check ."
    ],
    "tests": [
      "pytest -q"
    ]
  }
}
</META>

## PURPOSE
- Compute contiguous change blocks from ApplyResult and provide next/prev navigation with wrap.

## SCOPE
- In-scope:
  - Build blocks of added or removed lines
  - Provide navigation methods with wrap semantics
- Out-of-scope:
  - Parsing diffs
  - UI painting

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - from core.contracts import ApplyResult
- - from typing import List, Tuple

## CONSTANTS
- INDEX_BASE = 0

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- def analyze_changes(result: ApplyResult) -> list[tuple[int,int,str]]
  - pre: result valid; indices 0-based
  - post: returns blocks as (start,end,type)
  - errors: ValidationError on bad indices
- def next_change(current_line: int) -> int
  - pre: current_line >= 0
  - post: returns target line
  - errors: ValidationError on negatives
- def prev_change(current_line: int) -> int
  - pre: current_line >= 0
  - post: returns target line
  - errors: ValidationError on negatives
- analyze_changes consumes only result.added_lines and result.removed_original_indices (0-based)

## STATE
- blocks: list[tuple[int,int,str]]

## THREADING
- ui_thread_only: false
- worker_policy: none
- handoff: callback

## I/O
- inputs: ["ApplyResult"]
- outputs: ["blocks", "line indices"]
- encoding: utf-8
- atomic_write: false  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start ui.navigation"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) Merge adjacent indices of same type into blocks
2) Sort blocks by start
3) Implement wrap-around for next and previous

### EDGE CASES
- - No changes → return empty list
- - Current line beyond end → clamp to end
101) Merge from result.added_lines and result.removed_original_indices only

## ERRORS
- - ValidationError on unsorted indices

## COMPLEXITY
- time: O(n log n)
- memory: O(n)
- notes: none

## PERFORMANCE
- max input size: 200k indices
- max iterations: n
- timeout: none
- instrumentation:
- count blocks generated

## TESTS - ACCEPTANCE HOOKS
- assert wrap behavior consistent
- assert blocks non-overlapping
- assert all(a>=0 for a in result.added_lines)
- assert all(r>=0 for r in result.removed_original_indices)

## EXTENSIBILITY
- - Filtering by type can be added later

## NON-FUNCTIONAL
- security: none
- i18n: UTF-8