# Import Path Update Summary for new_system

## Overview
All import paths in the `elders_guild/new_system` directory have been updated to reflect the correct module structure.

## Changes Made

### 1. Quality Servants Module (`quality_servants/*.py`)
Updated imports from:
- `from elders_guild.quality.*` → `from elders_guild.new_system.quality.*`

Files updated:
- `comprehensive_guardian_servant.py`
- `quality_watcher_judgment.py`
- `quality_watcher_servant.py`
- `test_forge_judgment.py`
- `test_forge_servant.py`

### 2. Quality Module (`quality/*.py`)
Updated imports from:
- `from elders_guild.quality.*` → `from elders_guild.new_system.quality.*`
- `from elders_guild.quality_servants.*` → `from elders_guild.new_system.quality_servants.*`

Files updated:
- `unified_quality_pipeline.py` (10 import statements updated)

### 3. Test Files (`tests/quality/*.py`)
Updated imports from:
- `from elders_guild.quality_servants.*` → `from elders_guild.new_system.quality_servants.*`
- `from elders_guild.quality.*` → `from elders_guild.new_system.quality.*`

Files updated:
- `test_quality_servants_mock.py` (4 import statements updated)

### 4. Scripts (`scripts/*.sh`)
Updated module paths from:
- `elders_guild.quality.servants.*` → `elders_guild.new_system.quality_servants.*`
- `elders_guild.quality.*` → `elders_guild.new_system.quality.*`

Files updated:
- `start-quality-servants.sh` (5 module paths updated)

## Verification
All old import paths have been successfully replaced. No references to the old paths remain in the codebase.

## Usage
When importing modules from the new_system, always use the full path:
```python
# Correct
from elders_guild.new_system.quality.* import *
from elders_guild.new_system.quality_servants.* import *

# Incorrect (old paths)
from elders_guild.quality.* import *
from elders_guild.quality_servants.* import *
```

## Running Scripts
The updated scripts now use the correct module paths:
```bash
# Start quality servants
./scripts/start-quality-servants.sh

# Run quality pipeline
python3 -m elders_guild.new_system.quality.quality_pipeline_orchestrator run --path /path/to/project
```