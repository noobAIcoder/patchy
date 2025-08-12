# Navigation System Pseudocode

## NavigationManager Class

### Properties
- current_patch: FilePatch or None
- result: ApplyResult or None
- added_blocks: List[contiguous block starts]
- removed_blocks: List[contiguous block starts]

### Methods

#### update_for_patch(patch, apply_result)
1. STORE patch and result
2. BUILD added_blocks:
   - SORT added_lines
   - FIND contiguous blocks
   - STORE block start positions
3. BUILD removed_blocks:
   - SORT removed_lines_original
   - FIND contiguous blocks
   - STORE block start positions

#### create_widget()
1. CREATE QWidget
2. CREATE vertical layout
3. ADD navigation buttons:
   - Previous change
   - Next change
   - Jump to first/last
4. ADD change counter label
5. ADD keyboard shortcuts
6. RETURN widget

#### navigate_prev()
1. DETERMINES active editor (original or preview)
2. GET current cursor line
3. FIND previous block start before cursor
4. IF found:
   - MOVE cursor to block start
5. ELSE:
   - WRAP to last block

#### navigate_next()
1. DETERMINES active editor
2. GET current cursor line
3. FIND next block start after cursor
4. IF found:
   - MOVE cursor to block start
5. ELSE:
   - WRAP to first block

#### find_contiguous_blocks(indices)
1. INPUT: sorted list of indices
2. IF empty:
   RETURN empty list
3. INITIALIZE blocks = [indices[0]]
4. FOR each index starting from second:
   - IF index != previous + 1:
     - ADD index to blocks
5. RETURN blocks