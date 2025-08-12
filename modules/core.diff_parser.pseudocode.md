# Diff Parser Pseudocode

## Main Function: parse_diff_content
1. INPUT: diff_content (string)
2. IF diff_content is empty or only whitespace:
   RETURN empty list
3. SPLIT diff_content into lines
4. INITIALIZE:
   - patches = empty list
   - current_patch = None
   - index = 0
5. WHILE index < length(lines):
   - line = lines[index]
   - IF line should be skipped (matches skip prefixes):
     - index += 1
     - CONTINUE
   - IF line starts file header:
     - patch = parse_file_header(lines, index)
     - IF patch is valid:
       - APPEND patch to patches
       - SET current_patch = patch
       - index += 2  # Skip header pair
       - CONTINUE
   - IF line starts hunk header ('@@'):
     - IF current_patch is None:
       - RAISE ParseError("Hunk before file header")
     - hunk, consumed = parse_hunk(lines, index)
     - APPEND hunk to current_patch.hunks
     - index += consumed
     - CONTINUE
   - index += 1
6. RETURN patches

## Function: parse_file_header
1. INPUT: lines, start_index
2. IF start_index + 1 >= length(lines):
   RETURN None
3. DETECT header style:
   - IF line matches unified pattern ('---'):
     - old_path = extract path after '---'
     - EXPECT next line starts with '+++'
     - new_path = extract path after '+++'
   - ELIF line matches context pattern ('***'):
     - old_path = extract path after '***'
     - EXPECT next line starts with '---'
     - new_path = extract path after '---'
   - ELSE:
     RETURN None
4. CLEAN both paths:
   - Remove timestamp after tab
   - Remove 'a/' or 'b/' prefixes
   - Strip whitespace
5. RETURN FilePatch(old_path, new_path, [])

## Function: parse_hunk
1. INPUT: lines, start_index
2. header_line = lines[start_index]
3. PARSE header using regex:
   - Extract old_start (default 1)
   - Extract old_len (default 0)
   - Extract new_start (default 1)
   - Extract new_len (default 0)
4. CREATE hunk object with parsed values
5. index = start_index + 1
6. WHILE index < length(lines):
   - line = lines[index]
   - IF line starts new section:
     BREAK
   - IF line is empty:
     - ADD HunkLine(' ', '')
   - ELIF first character is in [' ', '+', '-']:
     - ADD HunkLine(kind, line[1:])
   - ELIF line is '\\ No newline...':
     - SKIP
   - ELSE:
     - RAISE ParseError("Invalid hunk line")
   - index += 1
7. RETURN (hunk, index - start_index)

## Function: should_skip_line
1. INPUT: line
2. FOR each skip_prefix in skip_prefixes:
   - IF line starts with skip_prefix:
     RETURN True
3. RETURN False

## Function: clean_path
1. INPUT: path_string
2. REMOVE everything after tab character
3. IF path starts with 'a/' or 'b/':
   - REMOVE first 2 characters
4. STRIP whitespace
5. RETURN cleaned path