# core.contracts - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "core.contracts",
  "target_file": "src/core/contracts.py",
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
- Provide shared dataclasses, exceptions, constants, logging bootstrap for Patchy modules.

## SCOPE
- In-scope:
  - Define FilePatch, Hunk, HunkLine, ApplyResult dataclasses
  - Provide exception hierarchy: PatchyError, ParseError, ApplyError, ValidationError, IOErrorCompat
  - Expose constants: SKIP_PREFIXES, UNIFIED_HUNK_HEADER_REGEX, CONTEXT_HUNK_HEADER_REGEX, INDEX_BASE, NEWLINE_POLICY
  - Initialize module logger 'patchy'
- Out-of-scope:
  - Business logic
  - Qt widgets
  - Disk I/O beyond reading config

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - from dataclasses import dataclass
- - from typing import Optional, List, Tuple, Dict, Any
- - import logging

## CONSTANTS
- SKIP_PREFIXES = ["diff --git ", "index ", "new file mode ", "deleted file mode ", "--- ", "+++ ", "*** ", "rename from ", "rename to ", "similarity index ", "Binary files "]
- UNIFIED_HUNK_HEADER_REGEX = "^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*$"
- CONTEXT_HUNK_HEADER_REGEX = "^\*\*\* (\d+),(\d+) \*\*\*\*$"
- INDEX_BASE = 0

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- class Contracts: ...
  - pre: none
  - post: types and constants are importable
  - errors: ValidationError on inconsistent constants


## STATE
- none: stateless

## THREADING
- ui_thread_only: false
- worker_policy: none
- handoff: callback

## I/O
- inputs: ["importers"]
- outputs: ["dataclasses", "exceptions", "constants"]
- encoding: utf-8
- atomic_write: false  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start core.contracts"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) Define dataclasses and exceptions
2) Define constants and export in __all__
3) Configure logger with INFO level by default
4) Return nothing

### EDGE CASES
- - Constants values must be import-safe strings or lists

## ERRORS
- - ValidationError when constants conflict (e.g., index_base not 0)

## COMPLEXITY
- time: O(1)
- memory: O(1)
- notes: none

## PERFORMANCE
- max input size: n/a
- max iterations: n/a
- timeout: none
- instrumentation:
- logging configured exactly once

## TESTS - ACCEPTANCE HOOKS
- assert types importable
- assert logger name equals 'patchy'
- assert INDEX_BASE == 0
- assert isinstance(SKIP_PREFIXES, list) and 'rename from ' in SKIP_PREFIXES and 'deleted file mode ' in SKIP_PREFIXES

## EXTENSIBILITY
- - New constants can be added without breaking imports

## NON-FUNCTIONAL
- security: no secrets
- i18n: UTF-8
- compliance: no telemetry