#!/usr/bin/env python3
"""
Migration script to transition from multiple Auto Issue Processor implementations
to the unified implementation
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Main migration function"""
    print("=" * 60)
    print("Auto Issue Processor Migration Tool")
    print("=" * 60)
    
    # Step 1: Backup existing implementations
    print("\n1. Backing up existing implementations...")
    backup_dir = Path("backups/auto_issue_processor_migration_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    old_implementations = [
        "libs/integrations/github/auto_issue_processor.py",
        "libs/integrations/github/auto_issue_processor_enhanced.py",
        "libs/integrations/github/enhanced_auto_issue_processor.py",
        "libs/integrations/github/auto_issue_processor_safegit_patch.py",
        "libs/optimized_auto_issue_processor.py"
    ]
    
    for impl in old_implementations:
        if os.path.exists(impl):
            dest = backup_dir / Path(impl).name
            shutil.copy2(impl, dest)
            print(f"   ✓ Backed up {impl}")
    
    # Step 2: Update scheduler references
    print("\n2. Updating scheduler references...")
    scheduler_file = "libs/elder_scheduled_tasks.py"
    if os.path.exists(scheduler_file):
        with open(scheduler_file, 'r') as f:
            content = f.read()
        
        # Replace old import
        old_import = "from libs.integrations.github.enhanced_auto_issue_processor import EnhancedAutoIssueProcessor"
        new_import = "from libs.auto_issue_processor import AutoIssueProcessor"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            content = content.replace("EnhancedAutoIssueProcessor", "AutoIssueProcessor")
            
            # Write back
            with open(scheduler_file, 'w') as f:
                f.write(content)
            print("   ✓ Updated scheduler imports")
        else:
            print("   - Scheduler already updated or using different import")
    
    # Step 3: Create migration notes
    print("\n3. Creating migration notes...")
    migration_notes = {
        "migration_date": datetime.now().isoformat(),
        "old_implementations": old_implementations,
        "new_implementation": "libs/auto_issue_processor/",
        "backup_location": str(backup_dir),
        "configuration_file": "configs/auto_issue_processor.yaml",
        "changes": [
            "Unified 5 different implementations into one",
            "Added centralized configuration management",
            "Implemented process locking to prevent conflicts",
            "Modularized features (error recovery, PR creation, parallel processing, 4 sages)",
            "Created comprehensive test suite"
        ],
        "migration_steps": [
            "1. Backup old implementations ✓",
            "2. Update scheduler references ✓", 
            "3. Update any custom scripts to use new import",
            "4. Review and update configuration file",
            "5. Test the new implementation",
            "6. Remove old implementations (after verification)"
        ]
    }
    
    notes_file = backup_dir / "migration_notes.json"
    with open(notes_file, 'w') as f:
        json.dump(migration_notes, f, indent=2)
    print(f"   ✓ Migration notes saved to {notes_file}")
    
    # Step 4: Configuration check
    print("\n4. Checking configuration...")
    config_file = "configs/auto_issue_processor.yaml"
    if os.path.exists(config_file):
        print(f"   ✓ Configuration file exists: {config_file}")
    else:
        print("   ⚠️  Configuration file not found. Please create it from the template.")
    
    # Step 5: Provide next steps
    print("\n" + "=" * 60)
    print("Migration preparation complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the configuration file: configs/auto_issue_processor.yaml")
    print("2. Update any custom scripts that import the old implementations")
    print("3. Test the new implementation:")
    print("   python3 -c 'from libs.auto_issue_processor import AutoIssueProcessor'")
    print("4. Re-enable the scheduler when ready")
    print("5. After verification, remove old implementations")
    print(f"\nBackup saved to: {backup_dir}")
    
    # Create a quick test script
    test_script = """#!/usr/bin/env python3
import asyncio
from libs.auto_issue_processor import AutoIssueProcessor, ProcessorConfig

async def test():
    config = ProcessorConfig()
    config.dry_run = True
    processor = AutoIssueProcessor(config)
    print("✓ Unified processor loaded successfully!")
    
asyncio.run(test())
"""
    
    test_file = Path("test_unified_import.py")
    with open(test_file, 'w') as f:
        f.write(test_script)
    test_file.chmod(0o755)
    print(f"\nCreated test script: {test_file}")
    print("Run it with: python3 test_unified_import.py")


if __name__ == "__main__":
    main()