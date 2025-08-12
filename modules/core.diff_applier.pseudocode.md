# core.diff_applier - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "core.diff_applier",
  "target_file": "src/core/diff_applier.py",
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
- Apply a parsed FilePatch to original text using strict or fuzzy anchoring and report line mappings.

## SCOPE
- In-scope:
  - Strict application of hunks
  - Fuzzy recovery within bounded window
  - Origin map generation
- Out-of-scope:
  - Parsing diffs
  - UI rendering

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - from core.contracts import FilePatch, Hunk, ApplyResult, ApplyError
- - from typing import List, Optional

## CONSTANTS
- INDEX_BASE = 0

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- def apply(original: str, patch: FilePatch, strict: bool = True) -> ApplyResult
  - pre: original LF normalized; patch well-formed
  - post: returns ApplyResult; origin_map length equals output line count
  - errors: ApplyError on context mismatch
- def preview(original: str, patch: FilePatch) -> ApplyResult
  - pre: same as apply
  - post: returns ApplyResult without writing
  - errors: none
- def calculate_guess_index(hunk: Hunk, prior_offset: int) -> int
  - pre: prior_offset is int
  - post: returns non-negative int
  - errors: ApplyError on negative result
- def fuzzy_context() -> int
  - pre: none
  - post: returns default fuzz window in lines
  - errors: none
- ApplyResult fields are 0-based and sorted: added_lines, removed_original_indices

## STATE
- window_bias: int - current guessed offset

## THREADING
- ui_thread_only: false
- worker_policy: none
- handoff: callback

## I/O
- inputs: ["original string", "FilePatch"]
- outputs: ["ApplyResult"]
- encoding: utf-8
- atomic_write: false  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start core.diff_applier"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) Split original into lines
2) For each hunk, locate anchor line using strict match else fuzzy within window
3) Apply additions and deletions, updating running offset
4) Track added_lines and removed_original_indices (0-based)
5) Build origin_map mapping output line to original or null
6) Return ApplyResult

### EDGE CASES
- - Empty patch → return original unchanged with empty deltas
- - Overlapping hunks → raise ApplyError
- - Excess fuzz window → clamp to limit

## ERRORS
- - ApplyError when context cannot be located
- - ValidationError when patch inconsistent

## COMPLEXITY
- time: O(n + m)
- memory: O(n + m)
- notes: none

## PERFORMANCE
- max input size: 50MB
- max iterations: bounded by window per hunk
- timeout: none
- instrumentation:
- count fuzzy attempts
- measure per-hunk search time

## TESTS - ACCEPTANCE HOOKS
- assert origin_map length equals output lines
- assert removed_original_indices sorted and unique
- assert sorted(result.removed_original_indices) == result.removed_original_indices
- assert len(result.origin_map) == len(result.text.splitlines())

## EXTENSIBILITY
- - Alternative search strategies can be injected later

## NON-FUNCTIONAL
- security: pure in-memory
- i18n: UTF-8
- compliance: no telemetry