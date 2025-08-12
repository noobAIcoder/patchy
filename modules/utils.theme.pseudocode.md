# utils.theme - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "utils.theme",
  "target_file": "src/utils/theme.py",
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
- Manage theme preference 'light'|'dark'|'auto' and provide palette to UI consumers.

## SCOPE
- In-scope:
  - Store current theme
  - Expose palette dict
  - Signal listeners via callback hooks
- Out-of-scope:
  - OS polling inside highlighters or editors

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - from typing import Literal, Dict

## CONSTANTS
- DEFAULT_THEME = 'auto'

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- def current() -> str
  - pre: state initialized
  - post: returns 'light'|'dark'|'auto'
  - errors: none
- def set(name: str) -> None
  - pre: name in {'light','dark','auto'}
  - post: updates theme and emits callback
  - errors: ValidationError on bad name
- def palette() -> dict
  - pre: current theme set
  - post: returns stable color mapping
  - errors: none


## STATE
- subs: list[callable] - registered listeners

## THREADING
- ui_thread_only: false
- worker_policy: none
- handoff: callback

## I/O
- inputs: ["theme name"]
- outputs: ["palette dict", "callbacks"]
- encoding: utf-8
- atomic_write: false  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start utils.theme"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) If name invalid raise ValidationError
2) Set internal theme
3) Notify subscribers
4) Return palette on request

### EDGE CASES
- - Unknown theme → ValidationError

## ERRORS
- - ValidationError on bad theme name

## COMPLEXITY
- time: O(1)
- memory: O(1)
- notes: none

## PERFORMANCE
- max input size: n/a
- max iterations: n/a
- timeout: none
- instrumentation:
- count theme changes

## TESTS - ACCEPTANCE HOOKS
- assert palette keys include background, foreground, added, removed

## EXTENSIBILITY
- - New palettes can be added by extending mapping

## NON-FUNCTIONAL
- security: no external IO
- i18n: UTF-8