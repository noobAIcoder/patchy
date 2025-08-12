# State Manager Pseudocode

## StateManager Class

### Properties
- config_dir: Path to config directory
- config_file: Path to state file
- state: Dict of current state

### Methods

#### __init__()
1. DETERMINE config directory:
   - Windows: %APPDATA%/Patchy
   - macOS: ~/Library/Application Support/Patchy
   - Linux: ~/.config/Patchy
2. CREATE directory if not exists
3. SET config_file = config_dir / 'state.json'

#### save_state(state_dict)
1. INPUT: state_dict containing:
   - window_size
   - window_position
   - root_folder
   - current_file
   - splitter_states
   - recent_files
   - theme_preference
2. TRY:
   - SERIALIZE state_dict to JSON
   - WRITE to config_file
3. CATCH IOError:
   - LOG warning
   - CONTINUE

#### load_state()
1. TRY:
   - IF config_file exists:
     - READ file content
     - PARSE JSON
     - RETURN state_dict
2. CATCH (FileNotFoundError, JSONDecodeError):
   - RETURN default state:
     - window_size: 1600x1000
     - window_position: center
     - theme: 'auto'
     - recent_files: []
3. RETURN empty dict on any other error

#### clear_state()
1. IF config_file exists:
   - DELETE file
2. RESET to default state

#### add_recent_file(file_path)
1. LOAD current recent_files
2. IF file_path exists in list:
   - MOVE to top
3. ELSE:
   - INSERT at top
   - TRUNCATE to max 10 files
4. SAVE state