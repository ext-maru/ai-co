# Elders Guild Command Naming Standard 📋

## 🎯 Overview

Elders Guildの統一コマンド命名規則と標準化ガイドライン。現在の混在する命名パターンを整理し、一貫性のあるユーザーエクスペリエンスを提供します。

## 🚨 Current State Analysis

### Identified Inconsistencies
- **Separator混在**: `ai_command.py` vs `ai-command` vs `aicommand`
- **重複機能**: `ai_send.py` + `ai-send` (同機能の異なる実装)
- **カテゴリ分散**: 関連機能が異なる命名パターンに散在
- **長さ不統一**: `ai_dlq.py` vs `ai_incident_knights.py`
- **Fantasy混在**: `ai-elf-forest` など非標準命名

### Current Command Count
- **commands/*.py**: 72ファイル (underscore pattern)
- **scripts/ai-***: 46ファイル (hyphen pattern)
- **ai_commands/*.sh**: 100+ファイル (mixed patterns)
- **重複・実験的**: 多数の一時ファイル

## 🎯 Unified Naming Convention

### **Core Design Principles**

1. **🔗 Consistent Separator**: Always use hyphens (`-`)
2. **📁 Logical Grouping**: Functional domain prefixes
3. **🏗️ Hierarchical Structure**: `ai-[domain]-[action]-[object]`
4. **📖 Self-Documenting**: Clear, descriptive names
5. **⚡ Reasonable Length**: 2-4 words maximum

### **Standard Command Structure**

```
ai-[domain]-[action]-[object]
│   │       │       │
│   │       │       └─ Target object (optional)
│   │       └───────── Action verb
│   └─────────────────── Functional domain
└─────────────────────── Universal prefix
```

## 📋 Domain Categories

### **System Domain** (`ai-system-*`)
**Purpose**: Core system operations and management

```bash
ai-system-start        # System startup
ai-system-stop         # System shutdown
ai-system-status       # System status check
ai-system-health       # Health monitoring
ai-system-monitor      # Continuous monitoring
ai-system-backup       # System backup
ai-system-update       # System updates
ai-system-config       # Configuration management
ai-system-restart      # Full system restart
ai-system-reset        # System reset
```

### **Task Domain** (`ai-task-*`)
**Purpose**: Task management and execution

```bash
ai-task-send           # Send new task
ai-task-list           # List all tasks
ai-task-info           # Task details
ai-task-retry          # Retry failed task
ai-task-cancel         # Cancel task
ai-task-queue          # Queue management
ai-task-queue-clear    # Clear task queue
ai-task-simulate       # Task simulation
ai-task-priority       # Set task priority
ai-task-schedule       # Schedule task execution
```

### **Worker Domain** (`ai-worker-*`)
**Purpose**: Worker management and scaling

```bash
ai-worker-list         # List workers
ai-worker-add          # Add worker
ai-worker-remove       # Remove worker
ai-worker-restart      # Restart worker
ai-worker-scale        # Scale workers
ai-worker-recover      # Worker recovery
ai-worker-monitor      # Worker monitoring
ai-worker-comm         # Worker communication
ai-worker-health       # Worker health check
ai-worker-stats        # Worker statistics
```

### **Knowledge Domain** (`ai-knowledge-*`)
**Purpose**: Knowledge management and learning

```bash
ai-knowledge-search    # Search knowledge base
ai-knowledge-update    # Update knowledge
ai-knowledge-export    # Export knowledge
ai-knowledge-import    # Import knowledge
ai-knowledge-clean     # Clean knowledge base
ai-knowledge-backup    # Backup knowledge
ai-knowledge-stats     # Knowledge statistics
```

### **RAG Domain** (`ai-rag-*`)
**Purpose**: RAG system operations

```bash
ai-rag-search          # RAG search
ai-rag-index           # Build RAG index
ai-rag-manage          # RAG management
ai-rag-update          # Update RAG data
ai-rag-wizard          # RAG wizard tools
ai-rag-test            # Test RAG system
ai-rag-optimize        # Optimize RAG performance
```

### **Elder Domain** (`ai-elder-*`)
**Purpose**: Elder Council and governance

```bash
ai-elder-council       # Elder council management
ai-elder-pm            # Elder PM integration
ai-elder-compliance    # Compliance checking
ai-elder-proactive     # Proactive monitoring
ai-elder-summon        # Summon elder council
ai-elder-consult       # Elder consultation
ai-elder-decision      # Elder decision system
```

### **Incident Domain** (`ai-incident-*`)
**Purpose**: Incident response and management

```bash
ai-incident-knights    # Incident knights system
ai-incident-auto       # Auto incident handling
ai-incident-report     # Create incident report
ai-incident-analyze    # Analyze incidents
ai-incident-recover    # Incident recovery
ai-incident-prevent    # Incident prevention
```

### **Development Domain** (`ai-dev-*`)
**Purpose**: Development tools and utilities

```bash
ai-dev-test            # Run tests
ai-dev-tdd             # TDD development helper
ai-dev-coverage        # Test coverage analysis
ai-dev-codegen         # Code generation
ai-dev-debug           # Debug utilities
ai-dev-logs            # Log management
ai-dev-clean           # Cleanup operations
ai-dev-lint            # Code linting
ai-dev-format          # Code formatting
```

### **API Domain** (`ai-api-*`)
**Purpose**: API and integration management

```bash
ai-api-status          # API status check
ai-api-health          # API health check
ai-api-reset           # Reset API
ai-api-docs            # API documentation
ai-api-test            # Test API endpoints
ai-api-monitor         # API monitoring
```

### **Integration Domain** (`ai-integration-*`)
**Purpose**: External system integrations

```bash
ai-integration-slack   # Slack integration
ai-integration-git     # Git integration
ai-integration-docker  # Docker integration
ai-integration-mcp     # MCP integration
ai-integration-test    # Test integrations
```

### **Interface Domain** (`ai-ui-*`)
**Purpose**: User interfaces and interaction

```bash
ai-ui-web              # Web interface
ai-ui-dashboard        # Dashboard interface
ai-ui-cli              # CLI interface tools
ai-ui-help             # Help system
ai-ui-config           # UI configuration
```

### **Documentation Domain** (`ai-docs-*`)
**Purpose**: Documentation and reporting

```bash
ai-docs-generate       # Generate documentation
ai-docs-export         # Export documentation
ai-docs-update         # Update documentation
ai-docs-serve          # Serve documentation
ai-docs-validate       # Validate documentation
```

### **Analytics Domain** (`ai-analytics-*`)
**Purpose**: Analytics and reporting

```bash
ai-analytics-report    # Create reports
ai-analytics-metrics   # Collect metrics
ai-analytics-stats     # Show statistics
ai-analytics-trend     # Trend analysis
ai-analytics-export    # Export analytics
```

## 🔄 Migration Strategy

### **Phase 1: Core Command Consolidation** (Week 1)

**Priority**: High-usage daily commands

```bash
# Current → New
ai_send.py + ai-send → ai-task-send
ai_start.py + ai-start → ai-system-start
ai_stop.py + ai-stop → ai-system-stop
ai_status.py + ai-status → ai-system-status
ai_workers.py → ai-worker-list
ai_logs.py + ai-logs → ai-dev-logs
```

**Implementation Steps**:
1. Create new unified command
2. Test functionality equivalence
3. Create backward compatibility aliases
4. Update primary documentation

### **Phase 2: Functional Domain Grouping** (Week 2)

**Priority**: Administrative and management commands

```bash
# Worker management consolidation
ai_worker_* → ai-worker-*
ai_worker_add.py → ai-worker-add
ai_worker_rm.py → ai-worker-remove
ai_worker_restart.py → ai-worker-restart
ai_worker_recovery.py → ai-worker-recover

# Elder council consolidation
ai_elder_* → ai-elder-*
ai_elder_council.py → ai-elder-council
ai_elder_pm.py → ai-elder-pm
ai_elder_proactive.py → ai-elder-proactive

# Knowledge management
ai_knowledge.py → ai-knowledge-search
ai_rag.py → ai-rag-manage
ai_rag_search.py → ai-rag-search
```

### **Phase 3: Specialized Commands** (Week 3)

**Priority**: Development and integration tools

```bash
# Development tools
ai_test.py → ai-dev-test
ai_debug.py → ai-dev-debug
ai_clean.py → ai-dev-clean

# API integrations
ai-slack-pm → ai-integration-slack
ai-docker → ai-integration-docker
ai-git → ai-integration-git

# Documentation
ai_document.py → ai-docs-generate
ai_report.py → ai-analytics-report
```

### **Phase 4: Cleanup and Optimization** (Week 4)

**Priority**: Remove duplicates and deprecated commands

```bash
# Remove deprecated versions
rm ai_send_fixed.py  # Consolidated into ai-task-send
rm ai-send-simple    # Consolidated into ai-task-send
rm duplicate test files

# Clean up experimental commands
# Archive fantasy-themed commands
# Consolidate auto-generated test scripts
```

## 🔧 Implementation Guidelines

### **Command File Structure**

```bash
# Preferred location: scripts/
scripts/ai-task-send
scripts/ai-system-start
scripts/ai-worker-list

# Legacy support: commands/ (with symlinks)
commands/ai_send.py → ../scripts/ai-task-send
```

### **Alias Management**

**Create comprehensive alias file**: `ai_commands/aliases.sh`

```bash
#!/bin/bash
# Elders Guild Command Aliases - Backward Compatibility

# Legacy command support
alias ai-send='ai-task-send'
alias ai-start='ai-system-start'
alias ai-stop='ai-system-stop'
alias ai-status='ai-system-status'
alias ai-workers='ai-worker-list'
alias ai-logs='ai-dev-logs'

# Convenience shortcuts
alias ai-s='ai-system-status'
alias ai-w='ai-worker-list'
alias ai-t='ai-task-list'
alias ai-h='ai-ui-help'

# Domain shortcuts
alias ai-sys='ai-system-'    # Tab completion for system commands
alias ai-task='ai-task-'     # Tab completion for task commands
alias ai-work='ai-worker-'   # Tab completion for worker commands
```

### **Shell Completion**

**Enhanced tab completion**: `ai_commands/completions.bash`

```bash
# Elders Guild Command Completion
_ai_completion() {
    local cur prev domains actions
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    domains="system task worker knowledge rag elder incident dev api integration ui docs analytics"

    case "$prev" in
        ai-system-*)
            actions="start stop status health monitor backup update config restart reset"
            ;;
        ai-task-*)
            actions="send list info retry cancel queue simulate priority schedule"
            ;;
        ai-worker-*)
            actions="list add remove restart scale recover monitor comm health stats"
            ;;
        *)
            actions="$domains"
            ;;
    esac

    COMPREPLY=($(compgen -W "$actions" -- "$cur"))
}

complete -F _ai_completion ai-system- ai-task- ai-worker- ai-knowledge- ai-rag- ai-elder- ai-incident- ai-dev- ai-api- ai-integration- ai-ui- ai-docs- ai-analytics-
```

## 📖 Documentation Standards

### **Command Help Format**

```bash
#!/bin/bash
# ai-task-send - Send task to Elders Guild
#
# USAGE:
#   ai-task-send [OPTIONS] <task_description>
#   ai-task-send [OPTIONS] --file <task_file>
#
# DESCRIPTION:
#   Sends a task to the Elders Guild system for processing.
#   Tasks are queued and distributed to available workers.
#
# OPTIONS:
#   -p, --priority LEVEL    Set task priority (low|medium|high|urgent)
#   -w, --worker TYPE       Target specific worker type
#   -f, --file FILE         Send task from file
#   -j, --json              Output in JSON format
#   -v, --verbose           Verbose output
#   -h, --help              Show this help
#
# EXAMPLES:
#   ai-task-send "Analyze system performance"
#   ai-task-send -p high "Critical bug fix needed"
#   ai-task-send --file task.txt --worker code_review
#
# SEE ALSO:
#   ai-task-list, ai-task-info, ai-worker-list
```

### **Naming Convention Enforcement**

**Pre-commit hook**: `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Check for naming convention violations

violations=()

# Check for old naming patterns
if git diff --cached --name-only | grep -E "commands/ai_.*\.py$"; then
    violations+=("Legacy underscore naming in commands/")
fi

# Check for inconsistent separators
if git diff --cached --name-only | grep -E "scripts/ai[A-Z]|scripts/ai_"; then
    violations+=("Inconsistent naming in scripts/")
fi

if [ ${#violations[@]} -gt 0 ]; then
    echo "❌ Naming convention violations detected:"
    for violation in "${violations[@]}"; do
        echo "  - $violation"
    done
    echo ""
    echo "Please follow Elders Guild naming standard:"
    echo "  - Use: ai-domain-action-object"
    echo "  - See: docs/AI_COMPANY_COMMAND_NAMING_STANDARD.md"
    exit 1
fi
```

## 📊 Migration Tracking

### **Progress Metrics**

```bash
# Command standardization progress
Total commands: 150+
Standardized: 0/150 (0%)
Phase 1 target: 30/150 (20%)
Phase 2 target: 80/150 (53%)
Phase 3 target: 120/150 (80%)
Phase 4 target: 150/150 (100%)
```

### **Quality Gates**

- ✅ **No duplicate functionality**: One canonical command per function
- ✅ **Consistent naming**: All commands follow `ai-domain-action` pattern
- ✅ **Complete documentation**: Every command has help and examples
- ✅ **Backward compatibility**: Legacy aliases maintain user workflows
- ✅ **Shell integration**: Tab completion and help integration

## 🎯 Success Criteria

### **User Experience Improvements**
1. **Discoverable**: `ai-task-<TAB>` shows all task commands
2. **Predictable**: Similar patterns across all domains
3. **Memorable**: Logical hierarchy aids memorization
4. **Consistent**: No confusion about which command to use

### **Developer Experience Improvements**
1. **Organized**: Clear file structure and grouping
2. **Maintainable**: Consistent patterns for new commands
3. **Testable**: Standard testing patterns for all commands
4. **Documented**: Self-documenting command structure

### **System Benefits**
1. **Reduced complexity**: Eliminate duplicate commands
2. **Better performance**: Optimized command resolution
3. **Easier onboarding**: New users learn pattern once
4. **Scalable growth**: Standard supports future expansion

---

**Implementation Status**: 🚧 Phase 1 Planning
**Target Completion**: 4 weeks
**Backward Compatibility**: 100% during transition
**Documentation**: Complete standard defined

**Next Actions**:
1. Begin Phase 1 core command consolidation
2. Create backward compatibility aliases
3. Update shell completion scripts
4. Begin user communication about changes
