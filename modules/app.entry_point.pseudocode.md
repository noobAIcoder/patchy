# [MODULE_SLUG] - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "app.entry_point",
  "target_file": "src/main.py",
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
- Start application: parse CLI, initialize logging, create main window, run event loop with graceful shutdown.

## SCOPE
- In-scope:
  - CLI parse
  - Global exception handler
  - Startup banner
  - Exit code propagation
- Out-of-scope:
  - Business logic
  - Heavy computation

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - import sys
- - import argparse
- - from core.contracts import PatchyError
- from PyQt6.QtWidgets import QApplication

## CONSTANTS
- APP_NAME = 'Patchy'

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- def main(argv: list[str]) -> int
  - pre: argv is list[str]
  - post: returns 0 on success else non-zero
  - errors: none


## STATE
- none: stateless

## THREADING
- ui_thread_only: true
- worker_policy: none
- handoff: n/a

## I/O
- inputs: ["argv"]
- outputs: ["exit code"]
- encoding: utf-8
- atomic_write: false  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start app.entry_point"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) Parse CLI args
2) Initialize logging
3) Create QApplication and MainWindow
4) Run event loop
5) Catch top-level exceptions, log, set exit code

### EDGE CASES
- - No args → default behavior
- - Unknown arg → exit with usage 2
101) Create QApplication before constructing MainWindow

## ERRORS
- - ValidationError on bad CLI combinations

## COMPLEXITY
- time: O(1)
- memory: O(1)
- notes: none

## PERFORMANCE
- max input size: n/a
- max iterations: n/a
- timeout: none
- instrumentation:
- record startup time

## TESTS - ACCEPTANCE HOOKS
- assert exit code semantics respected

## EXTENSIBILITY
- - Subcommands can be added later

## NON-FUNCTIONAL
- security: no elevated privileges
- i18n: UTF-8