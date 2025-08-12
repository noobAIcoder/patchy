#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Core diff parsing and application logic for Patchy.

This parser is tolerant and recognizes several header styles:

- Unified headers:
    --- <old_path>[\t<timestamp>]
    +++ <new_path>[\t<timestamp>]

- Context-like headers used by some tools with unified hunks:
    *** <old_path>[\t<timestamp>]
    --- <new_path>[\t<timestamp>]

It also skips common VCS noise lines (git: diff --git, index, new/deleted file
mode, similarity index, rename from/to, GIT binary patch; plus "Binary files ...").
Unified hunks remain in the @@ format; true context hunks are not parsed yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ---------- Diff model ----------

@dataclass
class HunkLine:
    kind: str  # ' ', '+', '-'
    text: str  # without the leading prefix char

@dataclass
class Hunk:
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    lines: List[HunkLine] = field(default_factory=list)

@dataclass
class FilePatch:
    old_path: Optional[str]
    new_path: Optional[str]
    hunks: List[Hunk] = field(default_factory=list)

class PatchParseError(Exception):
    pass

class PatchApplyError(Exception):
    pass

@dataclass
class ApplyResult:
    text: str
    added_lines: List[int]               # indices in the resulting text (0-based)
    removed_lines_original: List[int]    # indices in the ORIGINAL text (0-based)

# ---------- Parser ----------

class UnifiedDiffParser:
    # Guard against confusing context-diff hunk headers like "*** 1,5 ***"
    RE_OLD_UNIFIED = re.compile(r'^---\s+(?!\d)(?P<path>.+)$')
    RE_NEW_UNIFIED = re.compile(r'^\+\+\+\s+(?!\d)(?P<path>.+)$')

    # "Context-like" file header where old is "*** ..." and new is "--- ..."
    RE_OLD_CONTEXTISH = re.compile(r'^\*\*\*\s+(?!\d)(?P<path>.+)$')
    RE_NEW_CONTEXTISH = re.compile(r'^---\s+(?!\d)(?P<path>.+)$')

    # Accept hunk headers in these forms:
    #   @@ -A,B +C,D @@ ...
    #   @@ -A +C @@ ...
    #   @@                       - bare marker, no ranges
    # Trailing labels after the closing @@ are tolerated.
    RE_HUNK = re.compile(
        r'^@@(?:\s*-\s*(?P<o_start>\d+)(?:,(?P<o_len>\d+))?)?'
        r'(?:\s+\+\s*(?P<n_start>\d+)(?:,(?P<n_len>\d+))?)?'
        r'(?:\s*@@.*)?$'
    )

    # Lines to ignore entirely when scanning
    _SKIP_PREFIXES = (
        'diff ',              # diff --git a/... b/...
        'index ',             # index 123..456 100644
        'new file mode',      # new file mode 100644
        'deleted file mode',  # deleted file mode 100644
        'similarity index',   # similarity index 100%
        'rename from',        # rename from ...
        'rename to',          # rename to ...
        'GIT binary patch',   # start of git binary patches
        'Binary files ',      # Binary files a/... and b/... differ
    )

    @staticmethod
    def _clean_path(p: str) -> str:
        """
        Normalize header paths:
          - drop trailing timestamp after a tab
          - strip a/ and b/ prefixes
          - trim whitespace
        """
        p = p.rstrip()
        # Drop timestamp after a tab (diff -u format)
        if '\t' in p:
            p = p.split('\t', 1)[0].rstrip()

        # Common /dev/null placeholder should pass through as-is
        if p == '/dev/null':
            return p

        # Strip leading a/ or b/ that tools add
        if p.startswith('a/') or p.startswith('b/'):
            p = p[2:]

        return p.strip()

    def parse(self, text: str) -> List[FilePatch]:
        lines = text.splitlines()
        patches: List[FilePatch] = []
        cur_file: Optional[FilePatch] = None

        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip generic VCS noise lines
            if any(line.startswith(pref) for pref in self._SKIP_PREFIXES):
                i += 1
                continue

            # Accept either header style
            m_ctx_old = self.RE_OLD_CONTEXTISH.match(line)
            m_old = self.RE_OLD_UNIFIED.match(line)

            if m_ctx_old:
                # Expect a '--- <new>' next (context-ish header pair)
                old_path = self._clean_path(m_ctx_old.group('path'))
                i += 1
                if i >= len(lines) or not self.RE_NEW_CONTEXTISH.match(lines[i]):
                    raise PatchParseError('Expected --- <new> after *** <old>')
                m_new = self.RE_NEW_CONTEXTISH.match(lines[i])
                new_path = self._clean_path(m_new.group('path')) if m_new else None
                cur_file = FilePatch(old_path=old_path, new_path=new_path, hunks=[])
                patches.append(cur_file)
                i += 1
                continue

            if m_old:
                # Expect a '+++ <new>' next (unified header pair)
                old_path = self._clean_path(m_old.group('path'))
                # Look ahead a couple of lines to be forgiving
                j = i + 1
                found_new = None
                lookahead_limit = min(len(lines), i + 4)
                while j < lookahead_limit:
                    if any(lines[j].startswith(pref) for pref in self._SKIP_PREFIXES):
                        j += 1
                        continue
                    mn = self.RE_NEW_UNIFIED.match(lines[j])
                    if mn:
                        found_new = mn
                        break
                    break  # do not skip arbitrary lines unless they are known noise
                if not found_new:
                    raise PatchParseError('Expected +++ <new> after --- <old>')
                new_path = self._clean_path(found_new.group('path'))
                cur_file = FilePatch(old_path=old_path, new_path=new_path, hunks=[])
                patches.append(cur_file)
                i = j + 1
                continue

            if line.startswith('@@'):
                if cur_file is None:
                    raise PatchParseError('Hunk found before file headers')
                m = self.RE_HUNK.match(line)
                if not m:
                    raise PatchParseError(f'Bad hunk header: {line}')
                # Defaults for short or bare headers
                ostart = int(m.group('o_start') or '1')
                olen = int(m.group('o_len') or '0')
                nstart = int(m.group('n_start') or '1')
                nlen = int(m.group('n_len') or '0')
                cur_hunk = Hunk(ostart, olen, nstart, nlen, [])
                cur_file.hunks.append(cur_hunk)
                i += 1
                # Consume hunk body
                while i < len(lines):
                    l = lines[i]
                    # Next hunk or next file header starts
                    if l.startswith('@@') or self.RE_OLD_UNIFIED.match(l) or self.RE_OLD_CONTEXTISH.match(l) or l.startswith('diff '):
                        break
                    if l == '':
                        # treat naked empty line as blank context (forgiving)
                        cur_hunk.lines.append(HunkLine(' ', ''))
                    else:
                        ch = l[0]
                        if ch in (' ', '+', '-'):
                            cur_hunk.lines.append(HunkLine(ch, l[1:]))
                        else:
                            if l.startswith('\\ No newline at end of file'):
                                pass
                            else:
                                raise PatchParseError(f'Unexpected hunk content line: {l}')
                    i += 1
                continue

            # Nothing matched, advance
            i += 1

        if not patches:
            raise PatchParseError('No file patches found')
        return patches

# ---------- Applier with tolerant anchoring ----------

class DiffApplier:
    """
    Applies unified diffs with robust anchoring:

    - Anchors on the full sequence of original-consuming lines (' ' and '-'),
      with tolerant handling for runs of blank lines (diff blank context can
      match zero-or-more blanks in text).
    - Tries guessed index, then fuzzy window, then global scan.
    - Returns detailed ApplyResult with added and removed indices.
    """

    def __init__(self, fuzzy_context: int = 5):
        self.fuzzy_context = max(0, int(fuzzy_context))

    # Public API
    def apply(self, original_text: str, patch: FilePatch) -> ApplyResult:
        orig_lines = original_text.splitlines()
        # working buffer we mutate
        out = orig_lines[:]
        # mapping from current 'out' line to original index (or None for inserted lines)
        origin_map: List[Optional[int]] = list(range(len(orig_lines)))
        line_bias = 0
        added_lines: List[int] = []
        removed_original_indices: List[int] = []

        for hunk in patch.hunks:
            guess_index = max(0, min(len(out), (hunk.old_start - 1) + line_bias))
            anchor_index = self._find_hunk_anchor(out, hunk, guess_index)
            if anchor_index is None:
                raise PatchApplyError(
                    f"Failed to locate hunk starting at old:{hunk.old_start} (near line {guess_index + 1})"
                )

            # VERIFY (non-mutating)
            cur = anchor_index
            for hl in hunk.lines:
                if hl.kind == ' ':
                    if hl.text == '':
                        # tolerate zero-or-more blanks
                        while cur < len(out) and out[cur] == '':
                            cur += 1
                    else:
                        if cur >= len(out) or out[cur] != hl.text:
                            raise PatchApplyError(f'Context mismatch near line {cur + 1}')
                        cur += 1
                elif hl.kind == '-':
                    if cur >= len(out) or out[cur] != hl.text:
                        raise PatchApplyError(f'Deletion mismatch near line {cur + 1}')
                    cur += 1
                elif hl.kind == '+':
                    # insertions don't consume original
                    pass

            # APPLY (mutating)
            cur = anchor_index
            for hl in hunk.lines:
                if hl.kind == '':
                    if hl.text == '':
                        # skip any number of blanks in current buffer
                        while cur < len(out) and out[cur] == '':
                            cur += 1
                    else:
                        cur += 1
                elif hl.kind == '-':
                    # record original index if we have it
                    if 0 <= cur < len(origin_map):
                        oi = origin_map[cur]
                        if oi is not None:
                            removed_original_indices.append(oi)
                    # delete one line
                    del out[cur]
                    del origin_map[cur]
                    line_bias -= 1
                    # do not advance cur
                elif hl.kind == '+':
                    out.insert(cur, hl.text)
                    origin_map.insert(cur, None)
                    added_lines.append(cur)
                    cur += 1
                    line_bias += 1

        return ApplyResult(
            text='\n'.join(out),
            added_lines=added_lines,
            removed_lines_original=sorted(removed_original_indices)
        )

    # ---- anchoring helpers ----

    def _find_hunk_anchor(self, lines: List[str], hunk: Hunk, guess_index: int) -> Optional[int]:
        consuming = [hl for hl in hunk.lines if hl.kind in (' ', '-')]
        min_need = self._min_consuming_length(consuming)

        if not consuming:
            # insert-only hunk
            return max(0, min(len(lines), guess_index))

        max_start = max(0, len(lines) - min_need)
        guess = max(0, min(max_start, guess_index))

        # try guess
        if self._hunk_matches_from(lines, consuming, guess):
            return guess

        # fuzzy window
        for d in range(1, self.fuzzy_context + 1):
            left = guess - d
            if 0 <= left <= max_start and self._hunk_matches_from(lines, consuming, left):
                return left
            right = guess + d
            if 0 <= right <= max_start and self._hunk_matches_from(lines, consuming, right):
                return right

        # global scan
        for pos in range(0, max_start + 1):
            if self._hunk_matches_from(lines, consuming, pos):
                return pos

        return None

    @staticmethod
    def _min_consuming_length(consuming_lines: List[HunkLine]) -> int:
        need = 0
        for hl in consuming_lines:
            if hl.kind == '-':
                need += 1
            elif hl.kind == ' ':
                if hl.text != '':
                    need += 1
                # blank context can match zero-or-more blanks -> no strict need
        return need

    @staticmethod
    def _hunk_matches_from(lines: List[str], consuming_lines: List[HunkLine], start: int) -> bool:
        cur = start
        L = len(lines)
        for hl in consuming_lines:
            if hl.kind == ' ':
                if hl.text == '':
                    # consume zero-or-more blanks
                    while cur < L and lines[cur] == '':
                        cur += 1
                else:
                    if cur >= L or lines[cur] != hl.text:
                        return False
                    cur += 1
            else:  # '-'
                if cur >= L or lines[cur] != hl.text:
                    return False
                cur += 1
        return True

# ---------- Utilities ----------

def summarize_patch(fp: FilePatch) -> Tuple[int, int, int]:
    """
    Return (additions, deletions, hunk_count) for a FilePatch.
    """
    adds = dels = 0
    for h in fp.hunks:
        for ln in h.lines:
            if ln.kind == '+':
                adds += 1
            elif ln.kind == '-':
                dels += 1
    return adds, dels, len(fp.hunks)

def format_file_diff(fp: FilePatch) -> str:
    """
    Stringify a single-file unified diff (headers + hunks).
    Useful for the 'File diff' pane in the UI.
    """
    oldp = fp.old_path or "/dev/null"
    newp = fp.new_path or "/dev/null"
    out: List[str] = [f"--- a/{oldp}", f"+++ b/{newp}"]
    for h in fp.hunks:
        out.append(f"@@ -{h.old_start},{h.old_len} +{h.new_start},{h.new_len} @@")
        for ln in h.lines:
            out.append(f"{ln.kind}{ln.text}")
    return "\n".join(out)
