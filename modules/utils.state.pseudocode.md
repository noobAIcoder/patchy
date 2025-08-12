# utils.state - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "utils.state",
  "target_file": "src/utils/state.py",
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
- Persist and retrieve JSON state with atomic writes and schema validation.

## SCOPE
- In-scope:
  - Load/save JSON
  - Atomic temp-write and replace
  - Keyed sections: window, ui, files
- Out-of-scope:
  - YAML parsing
  - Secrets storage

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - from typing import Any, Optional, Dict
- - import json
- - from pathlib import Path
- - from core.contracts import ValidationError

## CONSTANTS
- STATE_FILE = 'patchy.state.json'
- INDEX_BASE = 0

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- def load(key: str) -> dict | None
  - pre: key in {'window','ui','files'}
  - post: returns dict or None
  - errors: ValidationError on unknown key
- def save(key: str, value: dict) -> None
  - pre: value JSON-serializable
  - post: file updated atomically
  - errors: IOErrorCompat on write fail
- def delete(key: str) -> None
  - pre: key valid
  - post: removes key
  - errors: IOErrorCompat on write fail
- def clear() -> None
  - pre: none
  - post: empties state file
  - errors: IOErrorCompat


## STATE
- cache: dict - optional in-memory cache

## THREADING
- ui_thread_only: false
- worker_policy: none
- handoff: callback

## I/O
- inputs: ["state path", "dict values"]
- outputs: ["state file"]
- encoding: utf-8
- atomic_write: true  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start utils.state"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) Resolve state file path
2) Read JSON if exists else default {}
3) Validate schema per key
4) Write via temp file then replace

### EDGE CASES
- - Missing file → return defaults
- - Corrupt JSON → raise ValidationError
- - Permission denied → IOErrorCompat

## ERRORS
- - ValidationError on schema mismatch
- - IOErrorCompat on filesystem errors

## COMPLEXITY
- time: O(n)
- memory: O(n)
- notes: none

## PERFORMANCE
- max input size: 1MB
- max iterations: n
- timeout: none
- instrumentation:
- count reads and writes

## TESTS - ACCEPTANCE HOOKS
- assert round-trip save-load yields identical dict
- assert save()->load() round-trip equals input dict
- assert atomic write leaves valid file after simulated crash

## EXTENSIBILITY
- - New keys can be added without breaking existing state

## NON-FUNCTIONAL
- security: prevent path traversal
- i18n: UTF-8
- compliance: no secrets in state