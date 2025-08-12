# [MODULE_SLUG] - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "ui.code_editor",
  "target_file": "src/ui/code_editor.py",
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
- Provide a text editor widget API with line navigation, highlights, and change notifications.

## SCOPE
- In-scope:
  - Set/get content
  - Scroll to line
  - Highlight lines
  - Emit signals on edits
- Out-of-scope:
  - Disk I/O
  - Diff parsing

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - from typing import List
- - from core.contracts import ValidationError

## CONSTANTS
- HIGHLIGHT_LIMIT = 20000

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- def set_content(content: str) -> None
  - pre: content is str; LF normalized
  - post: content stored; signals emitted
  - errors: ValidationError on None
- def get_content() -> str
  - pre: content may be empty
  - post: returns string
  - errors: none
- def scroll_to_line(line: int, centered: bool = True) -> None
  - pre: line >= 0
  - post: viewport moved
  - errors: ValidationError if out of range
- def highlight_lines(lines: list[int]) -> None
  - pre: all >= 0
  - post: applies highlight up to HIGHLIGHT_LIMIT
  - errors: ValidationError on negatives
- Signals: on_content_changed(str), on_cursor_moved(int,int), on_scroll(int,int)

## STATE
- content: str
- highlights: list[int]

## THREADING
- ui_thread_only: true
- worker_policy: none
- handoff: queued signal

## I/O
- inputs: ["strings", "line indices"]
- outputs: ["signals"]
- encoding: utf-8
- atomic_write: false  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start ui.code_editor"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) Normalize input newlines to LF
2) Set internal buffer
3) Emit onContentChanged
4) Scroll and highlight as requested with bounds checks

### EDGE CASES
- - Empty content → still valid
- - Out-of-range line → ValidationError

## ERRORS
- - ValidationError on bad params

## COMPLEXITY
- time: O(n)
- memory: O(n)
- notes: none

## PERFORMANCE
- max input size: 10MB
- max iterations: n
- timeout: none
- instrumentation:
- count highlights applied

## TESTS - ACCEPTANCE HOOKS
- assert no ERROR logs during typical operations
- assert set(['on_content_changed','on_cursor_moved','on_scroll']) == set(defined_signals)

## EXTENSIBILITY
- - Future syntax highlight strategies can inject color providers

## NON-FUNCTIONAL
- security: none
- i18n: UTF-8 only