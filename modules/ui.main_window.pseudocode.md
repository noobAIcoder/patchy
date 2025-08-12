# [MODULE_SLUG] - Codegen-Ready Pseudocode Template
<!--
Purpose: A generic, reusable pseudocode spec that is strict enough for LLM codegen and CI enforcement.
Usage: Copy this file, replace bracketed placeholders, and keep comments that help future readers or tools.
Style: Deterministic, implementation-neutral, minimal ambiguity. Prefer lists and JSON blocks over prose.
-->

<META json>
{
  "slug": "ui.main_window",
  "target_file": "src/ui/main_window.py",
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
- Assemble main UI, wire signals, orchestrate file open, diff parse/apply, navigation, and state/theme integration.

## SCOPE
- In-scope:
  - Toolbar actions
  - Split panes
  - Open file/folder/diff
  - Apply patch
  - Persist and restore state
- Out-of-scope:
  - Implement diff parsing or applying logic inside
  - Network access

## IMPORTS - ALLOWED ONLY
<!-- Keep this list tight to avoid unreviewed dependencies creeping in. -->
- - from core.contracts import PatchyError
- - from typing import Optional
- from core.diff_parser import parse
- from core.diff_applier import apply
- from utils.state import load, save
- from utils.theme import current, palette
- from ui.code_editor import set_content, get_content, scroll_to_line, highlight_lines
- from ui.highlighters import set_palette, highlight_diff, highlight_patch
- from ui.navigation import analyze_changes, next_change, prev_change

## CONSTANTS
- SPLITTER_DEFAULTS = [300, 400, 300]

## TYPES - USE ONLY SHARED TYPES
<!-- Reference canonical shared types. Do not redefine here. -->
- Uses: FilePatch, Hunk, HunkLine, ApplyResult, ParseError, ApplyError  // from core.contracts

## INTERFACES
- def init_ui() -> None
  - pre: called once
  - post: widgets constructed and connected
  - errors: none
- def load_state() -> None
  - pre: state accessible
  - post: restore splitter sizes and theme
  - errors: none
- def save_state() -> None
  - pre: on close
  - post: persist state
  - errors: none
- def on_open_file(path: str) -> None
  - pre: path exists
  - post: file loaded and editors updated
  - errors: IOErrorCompat on fail
- def on_apply_diff() -> None
  - pre: diff present
  - post: apply result updates preview and nav
  - errors: ApplyError on failure


## STATE
- widgets: dict - references to editors and panels

## THREADING
- ui_thread_only: true
- worker_policy: threadpool
- handoff: queued signal

## I/O
- inputs: ["user actions", "paths"]
- outputs: ["signals", "editor content updates"]
- encoding: utf-8
- atomic_write: false  // temp file + replace

## LOGGING
- logger: patchy
- on_start: INFO "start ui.main_window"
- on_warn: WARNING "condition"
- on_error: ERROR "condition raises ErrorType"

## ALGORITHM
1) Construct widgets and connect signals
2) Wire state load and theme hookup
3) Handle file open and update editors
4) Invoke parser and applier in worker then post results to UI
5) Persist state on exit

### EDGE CASES
- - Missing file → show error
- - Parse error → show message and keep state stable
- - Apply error → revert preview

## ERRORS
- - IOErrorCompat, ParseError, ApplyError

## COMPLEXITY
- time: O(1) per event
- memory: O(1) steady aside from loaded files
- notes: none

## PERFORMANCE
- max input size: files up to 50MB
- max iterations: n/a
- timeout: none
- instrumentation:
- count UI events
- latency per apply

## TESTS - ACCEPTANCE HOOKS
- assert no ERROR logs during normal operations
- assert call order: open -> parse -> apply -> navigation -> editors updated
- assert no ERROR logs on success path

## EXTENSIBILITY
- - New panes can be added via widget registry

## NON-FUNCTIONAL
- security: path validation
- i18n: UTF-8 only
- compliance: no telemetry