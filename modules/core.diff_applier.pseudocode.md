# Diff Applier Pseudocode

## Main Function: apply_patch
1. INPUT: original_text (string), file_patch (FilePatch)
2. SPLIT original_text into lines
3. INITIALIZE:
   - result_lines = copy of original_lines
   - added_lines = empty list
   - removed_original_indices = empty list
   - line_bias = 0
   - origin_map = [0, 1, 2, ...]  # Maps result index to original index
4. FOR each hunk in file_patch.hunks:
   - guess_index = calculate_guess_index(hunk, line_bias)
   - anchor_index = find_anchor_index(result_lines, hunk, guess_index)
   - IF anchor_index is None:
     - RAISE ApplyError("Cannot locate hunk")
   - VERIFY hunk matches at anchor_index:
     - IF verification fails:
       - RAISE ApplyError("Context mismatch")
   - APPLY hunk:
     - FOR each hunk_line in hunk.lines:
       - IF hunk_line.kind == ' ':
         - IF hunk_line.text is empty:
           - SKIP any blank lines
         - ELSE:
           - ADVANCE cursor
       - ELIF hunk_line.kind == '-':
         - RECORD original index from origin_map
         - DELETE line from result_lines
         - DELETE from origin_map
         - DECREMENT line_bias
       - ELIF hunk_line.kind == '+':
         - INSERT line into result_lines
         - INSERT None into origin_map
         - ADD current index to added_lines
         - INCREMENT line_bias
5. RETURN ApplyResult(joined_lines, added_lines, sorted(removed_original_indices))

## Function: find_anchor_index
1. INPUT: lines, hunk, guess_index
2. consuming_lines = filter hunk.lines for [' ', '-'] types
3. IF no consuming_lines:
   - RETURN max(0, min(length(lines), guess_index))
4. min_needed = calculate_min_needed(consuming_lines)
5. max_start = max(0, length(lines) - min_needed)
6. guess = clamp(guess_index, 0, max_start)
7. IF hunk_matches_at(lines, consuming_lines, guess):
   - RETURN guess
8. TRY fuzzy search within fuzzy_context of guess
9. IF found, RETURN found index
10. TRY global scan of entire file
11. IF found, RETURN found index
12. RETURN None

## Function: hunk_matches_at
1. INPUT: lines, consuming_lines, start_pos
2. cursor = start_pos
3. FOR each line in consuming_lines:
   - IF line.kind == ' ':
     - IF line.text is empty:
       - SKIP any blank lines
     - ELSE:
       - IF cursor >= length(lines) OR lines[cursor] != line.text:
         - RETURN False
       - cursor += 1
   - ELIF line.kind == '-':
     - IF cursor >= length(lines) OR lines[cursor] != line.text:
       - RETURN False
     - cursor += 1
4. RETURN True

## Function: calculate_min_needed
1. INPUT: consuming_lines
2. needed = 0
3. FOR each line in consuming_lines:
   - IF line.kind == '-':
     - needed += 1
   - ELIF line.kind == ' ' AND line.text != '':
     - needed += 1
4. RETURN needed