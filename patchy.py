#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Core diff parsing and application logic for Patchy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Iterable


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
    added_lines: List[int]          # indices in the resulting text (0-based)
    removed_lines_original: List[int]  # indices in the ORIGINAL text (0-based)


# ---------- Parser ----------

class UnifiedDiffParser:
    RE_FROM = re.compile(r'^---\s+(?P<path>.+)$')
    RE_TO = re.compile(r'^\+\+\+\s+(?P<path>.+)$')
    RE_HUNK = re.compile(
        r'^@@\s*-\s*(?P<o_start>\d+)(?:,(?P<o_len>\d+))?\s+\+\s*(?P<n_start>\d+)(?:,(?P<n_len>\d+))?\s*@@'
    )

    @staticmethod
    def _clean_path(p: str) -> str:
        p = p.strip()
        if p.startswith("a/") or p.startswith("b/"):
            return p[2:]
        return p

    def parse(self, text: str) -> List[FilePatch]:
        lines = text.splitlines()
        patches: List[FilePatch] = []
        cur_file: Optional[FilePatch] = None
        cur_hunk: Optional[Hunk] = None

        i = 0
        while i < len(lines):
            line = lines[i]

            if line.startswith('diff '):
                i += 1
                continue

            if line.startswith('---'):
                m = self.RE_FROM.match(line)
                if not m:
                    raise PatchParseError(f'Bad --- line: {line}')
                old_path = self._clean_path(m.group('path'))
                i += 1
                if i >= len(lines) or not lines[i].startswith('+++'):
                    raise PatchParseError('Expected +++ after ---')
                m2 = self.RE_TO.match(lines[i])
                if not m2:
                    raise PatchParseError(f'Bad +++ line: {lines[i]}')
                new_path = self._clean_path(m2.group('path'))
                cur_file = FilePatch(old_path=old_path, new_path=new_path, hunks=[])
                patches.append(cur_file)
                cur_hunk = None
                i += 1
                continue

            if line.startswith('@@'):
                if cur_file is None:
                    raise PatchParseError('Hunk found before file headers')
                m = self.RE_HUNK.match(line)
                if not m:
                    raise PatchParseError(f'Bad hunk header: {line}')
                ostart = int(m.group('o_start'))
                olen = int(m.group('o_len') or '0')
                nstart = int(m.group('n_start'))
                nlen = int(m.group('n_len') or '0')
                cur_hunk = Hunk(ostart, olen, nstart, nlen, [])
                cur_file.hunks.append(cur_hunk)
                i += 1
                while i < len(lines):
                    l = lines[i]
                    if l.startswith('@@') or l.startswith('---') or l.startswith('diff '):
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
                if hl.kind == ' ':
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

        return ApplyResult(text='\n'.join(out), added_lines=added_lines,
                           removed_lines_original=sorted(removed_original_indices))

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
