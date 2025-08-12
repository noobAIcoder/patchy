# AGENT.md — Patchy Codegen Agent Contract (Python 3.11, PyQt6)

> Single source of truth for converting codegen-ready pseudocode in `/modules/*.pseudocode.md` into production Python in `/src/` with tests in `/tests/`.
> This file is loaded for every Codex Cloud task.

## 0. Operating Mode
- **Language**: Python 3.11
- **UI stack**: PyQt6 (widgets; no async GUI frameworks)
- **Test**: pytest
- **Lint/Format**: ruff (`ruff check .` and `ruff format --check .`)
- **Filesystem layout**:
  - Input pseudocode: `/modules/{slug}.pseudocode.md`
  - Output code: `/src/{path}.py` (exact path comes from META.target_file)
  - Output tests: `/tests/test_{slug}.py`

## 1. Pseudocode DSL the agent must follow
The source files contain this structure (sections are mandatory unless noted):
- `<META json> ... </META>` — machine-readable. Must be parsed and used verbatim.
  - Keys: `slug`, `target_file`, `language`, `runtime.python`, `index_base`, `newline`, `dependencies`, `acceptance.lint`, `acceptance.tests`
- `## PURPOSE` — produce a module that does exactly this and nothing more.
- `## SCOPE` — enforce **in-scope** and reject **out-of-scope** behavior.
- `## IMPORTS - ALLOWED ONLY` — only import from these modules. Prefer absolute imports under `src/` layout (e.g., `from core.contracts import ...`) mapped to package root.
- `## CONSTANTS` — copy verbatim; do not modify names or values.
- `## TYPES - USE ONLY SHARED TYPES` — use types from `core.contracts` where referenced.
- `## INTERFACES` — treat each bullet as a concrete signature; implement exactly. Respect pre/post/error contracts.
- `## STATE` — implement state exactly as specified; no hidden globals.
- `## THREADING` — adhere to policy. UI thread only mutates widgets; heavy work in worker threads.
- `## I/O` — only the specified inputs/outputs/side effects. Newline policy: normalize to **LF** on read; write **LF**; preserve final newline.
- `## LOGGING` — use `logging.getLogger("patchy")`. Log INFO at start, WARNING for recoverable issues, ERROR before raising exceptions.
- `## ALGORITHM`, `### EDGE CASES`, `## ERRORS`, `## COMPLEXITY`, `## PERFORMANCE`, `## TESTS - ACCEPTANCE HOOKS`, `## EXTENSIBILITY`, `## NON-FUNCTIONAL` — implement and honor all items.

## 2. Global Conventions (enforced)
- **Dataclasses**: use Python `@dataclass` for `FilePatch`, `Hunk`, `HunkLine`, `ApplyResult` (declared in `core.contracts`).
- **Exceptions**: raise only from the hierarchy (`PatchyError`, `ParseError`, `ApplyError`, `ValidationError`, `IOErrorCompat`).
- **Indices**: all line indices are **0-based** (`INDEX_BASE=0`). Document in code.
- **EOL**: read-normalize to LF; write LF; preserve trailing newline where applicable.
- **Determinism**: no randomness, no time-sensitive formatting in code paths under test.
- **Threading**: UI widgets and signals on GUI thread; background work via `concurrent.futures.ThreadPoolExecutor` with marshaling back to the UI thread using Qt queued calls (`QMetaObject.invokeMethod`/`QTimer.singleShot` or an equivalent signal bridge). Never block the UI thread with long work.
- **Logging**: do not print; use `logging`. Include start/warn/error markers noted in pseudocode.
- **No hidden dependencies**: only imports listed under `IMPORTS - ALLOWED ONLY`.
- **No API drift**: function/class names and signatures must match pseudocode exactly.

## 3. File and Package Mapping
- Treat `src/` as the project root package. Example: `src/core/contracts.py` is importable as `core.contracts`.
- Do not create new top-level packages or nested packages not implied by `target_file`.
- For each pseudocode file:
  - Write exactly **one** `.py` module to `META.target_file`.
  - Write exactly **one** test file to `/tests/test_{slug}.py`.

## 4. Test Generation Rules
- Convert **## TESTS - ACCEPTANCE HOOKS** bullets into concrete `pytest` tests.
- Use deterministic fixtures (small inline content). Do not hit the network or filesystem unless allowed by the module’s I/O.
- For UI tests, focus on logic-level verification (signals emitted, function outputs) rather than rendering.
- Ensure full test isolation and idempotence. No global state leaks across tests.
- Respect linting: generated tests must also pass ruff.

## 5. Module-Specific Guidance (common patterns)
- **core.contracts**: define dataclasses, constants (e.g., `SKIP_PREFIXES`, `UNIFIED_HUNK_HEADER_REGEX`, `CONTEXT_HUNK_HEADER_REGEX`, `INDEX_BASE`, `NEWLINE_POLICY`), exception classes, and a `get_logger()` helper returning `logging.getLogger("patchy")` configured once.
- **core.diff_parser**: implement exact unified/context diff grammar using constants; build `FilePatch`/`Hunk`/`HunkLine`; keep order stable; strict validation; no filesystem writes.
- **core.diff_applier**: implement strict-and-fuzzy application with bounded search; produce `ApplyResult` with `added_lines`, `removed_original_indices`, and `origin_map`; enforce 0-based, sorted indices.
- **utils.state**: JSON-only, atomic writes (temp + replace), schema-lite validation per key; no YAML.
- **utils.theme**: single source of palette; publish changes via callbacks or a small signal bridge (no OS polling here).
- **ui.code_editor**: define explicit signals `on_content_changed(str)`, `on_cursor_moved(int,int)`, `on_scroll(int,int)`; validate indices; LF-only content.
- **ui.highlighters**: consume palette from Theme; batch large updates; no OS detection.
- **ui.navigation**: compute contiguous blocks from `ApplyResult.added_lines` and `.removed_original_indices`; provide wrap-around next/prev.
- **ui.main_window**: orchestrate collaborators; all heavy work in workers; safe error surfaces; save/restore state; connect/disconnect signals cleanly.
- **app.entry_point**: parse CLI, bootstrap logging, create `QApplication` before widgets, safe shutdown with exit code.

## 6. Failure Policy
- If a pseudocode section contradicts another, prefer: CONSTANTS > INTERFACES > ALGORITHM > SCOPE > PURPOSE.
- If a section is missing, **fail the task** with a clear explanation rather than inventing behavior.
- If allowed imports are insufficient to satisfy the interfaces, fail with a deterministic list of missing imports.

## 7. Output Requirements
- The generated module file must be **complete and runnable** without manual edits.
- Every public function/class must have a short docstring reflecting pre/post/error conditions.
- Include `from __future__ import annotations` where useful.
- **All** logging, warnings, and significant actions must be issued via the module logger.
- Tests must pass: run `pytest -q` for the specific file and ensure `ruff check .` passes.

## 8. Command Map (what Codex Cloud should run)
- Lint: `python -m ruff check . && python -m ruff format --check .`
- Tests (single module): `pytest -q tests/test_{slug}.py`
- Full suite (optional): `pytest -q`

## 9. Examples of transforming acceptance hooks to tests
Given a hook: `- assert len(result.origin_map) == len(result.text.splitlines())`  
Produce a pytest test:
```python
def test_origin_map_length_matches_output(apply_sample):
    result = apply_sample()
    assert len(result.origin_map) == len(result.text.splitlines())
```

## 10. Prohibited Behaviors
- No third-party dependencies not listed in `IMPORTS - ALLOWED ONLY`.
- No network or disk access outside declared I/O.
- No random sleeps, time-based variability, or OS-specific assumptions without guards.
- No mutation of other modules unless explicitly allowed by SCOPE.

---

**End of AGENT.md.** The agent must treat this document as normative and refuse ambiguous generation rather than guessing.