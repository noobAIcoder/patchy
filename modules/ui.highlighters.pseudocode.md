# ui.highlighters - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "ui.highlighters",
  "target_file": "src/ui/highlighters.py",
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
- Render visual styles for diff and code regions based on Theme palette; no OS detection here.

## SCOPE
- In-scope:
  - Apply styles for added, removed, headers, line numbers
  - Batch updates to avoid jank
- Out-of-scope:
  - Theme detection
  - File I/O

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - from typing import List
- - from core.contracts import ValidationError

## CONSTANTS
- BATCH_SIZE = 1000
- DELAY_MS = 0

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- def set_palette(palette: dict) -> None
  - pre: required keys present: {'background','foreground','added','removed','header','lineNumber','selection'}
  - post: palette stored
  - errors: ValidationError on missing keys
- def highlight_diff(lines: list[str]) -> None
  - pre: lines is list[str]
  - post: styles applied
  - errors: none
- def highlight_patch(added: list[int], removed: list[int]) -> None
  - pre: indices >= 0
  - post: styles applied
  - errors: ValidationError on negatives


## STATE
- palette: dict

## THREADING
- ui_thread_only: true
- worker_policy: none
- handoff: queued signal

## I/O
- inputs: ["palette dict", "text lines", "indices"]
- outputs: ["styled regions"]
- encoding: utf-8
- atomic_write: false  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start ui.highlighters"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) Validate palette keys exist
2) Apply styles in batches of BATCH_SIZE
3) Optionally delay between batches via DELAY_MS

### EDGE CASES
- - Empty lines → no-op
- - Missing palette key → ValidationError

## ERRORS
- - ValidationError on bad inputs

## COMPLEXITY
- time: O(n)
- memory: O(1)
- notes: none

## PERFORMANCE
- max input size: 200k lines
- max iterations: n
- timeout: none
- instrumentation:
- count batches

## TESTS - ACCEPTANCE HOOKS
- assert indices are 0-based and sorted

## EXTENSIBILITY
- - New token categories can be added by extending key map

## NON-FUNCTIONAL
- security: none
- i18n: UTF-8