# [MODULE_SLUG] - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "core.diff_parser",
  "target_file": "src/core/diff_parser.py",
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
- Parse unified or context diff text into structured FilePatch and Hunk objects.

## SCOPE
- In-scope:
  - Parse headers, file sections, and hunks
  - Skip noise lines using SKIP_PREFIXES
  - Normalize EOL to LF
- Out-of-scope:
  - Applying patches
  - Filesystem writes

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - from core.contracts import FilePatch, Hunk, HunkLine, ParseError, UNIFIED_HUNK_HEADER_REGEX, CONTEXT_HUNK_HEADER_REGEX, SKIP_PREFIXES
- - from typing import List, Tuple
- - import re

## CONSTANTS
- UNIFIED_HUNK_HEADER_REGEX = "^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*$"
- CONTEXT_HUNK_HEADER_REGEX = "^\*\*\* (\d+),(\d+) \*\*\*\*$"
- SKIP_PREFIXES = ["diff --git ", "index ", "new file mode ", "deleted file mode ", "--- ", "+++ ", "*** ", "rename from ", "rename to ", "similarity index ", "Binary files "]
- INDEX_BASE = 0

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- def parse(content: str) -> list[FilePatch]
  - pre: content is str; not None; LF normalized
  - post: returns list of FilePatch; stable order by appearance
  - errors: ParseError on grammar violation
- def validate(content: str) -> tuple[bool, list[tuple[int,str]]]
  - pre: content is str
  - post: returns validity and sorted error list
  - errors: none
- def split_lines(content: str) -> list[str]  - pre: content is str; post: LF-only lines; errors: none

## STATE
- line_no: int - current line index

## THREADING
- ui_thread_only: false
- worker_policy: none
- handoff: callback

## I/O
- inputs: ["diff content string"]
- outputs: ["list[FilePatch]"]
- encoding: utf-8
- atomic_write: false  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start core.diff_parser"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) Split content into lines with LF
2) Iterate, skipping SKIP_PREFIXES and non-hunk noise
3) Detect file boundaries and create FilePatch entries
4) Match hunk headers via UNIFIED_HUNK_HEADER_REGEX or CONTEXT_HUNK_HEADER_REGEX
5) Accumulate HunkLine with kinds ' ', '+', '-'
6) Validate counts against header spans
7) Return FilePatch list

### EDGE CASES
- - Empty content → return []
- - Malformed header → raise ParseError with line number
- - Unknown line kind → raise ParseError

## ERRORS
- - ParseError when grammar is violated

## COMPLEXITY
- time: O(n)
- memory: O(n)
- notes: none

## PERFORMANCE
- max input size: 50MB
- max iterations: n
- timeout: none
- instrumentation:
- count lines processed
- record header matches

## TESTS - ACCEPTANCE HOOKS
- assert lines count equals sum of hunks
- assert only kinds in {' ', '+', '-'}
- assert re.compile(UNIFIED_HUNK_HEADER_REGEX)
- assert all(k in {' ', '+', '-'} for fp in parse(sample) for h in fp.hunks for k in [ln.kind for ln in h.lines])

## EXTENSIBILITY
- - Add context-diff support without changing parse signature

## NON-FUNCTIONAL
- security: no file paths are executed
- i18n: UTF-8 only
- compliance: no telemetry