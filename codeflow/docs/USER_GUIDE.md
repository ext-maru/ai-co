# Elders Guild CodeFlow User Guide

Welcome to Elders Guild CodeFlow! This guide will help you get started and make the most of the extension.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Commands](#commands)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Installation

### From VS Code Marketplace

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Elders Guild CodeFlow"
4. Click Install

### From VSIX File

1. Download the `.vsix` file
2. Open VS Code
3. Go to Extensions (Ctrl+Shift+X)
4. Click "..." menu → "Install from VSIX..."
5. Select the downloaded file

## Quick Start

1. **Open Command Palette**: Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. **Type "CodeFlow"**: You'll see all available commands
3. **Try Natural Language**: Press `Ctrl+Shift+N` and type what you want to do

### First Steps

1. **Check System Status**
   - Press `Ctrl+Shift+S`
   - Or click the AI status in the status bar

2. **Browse Commands**
   - Press `Ctrl+Shift+A`
   - Or use the CodeFlow sidebar

3. **Execute a Command**
   - Select any command from the list
   - View results in a new document

## Features

### 🤖 Natural Language Commands

Instead of remembering exact command names, just describe what you want:

- "show system status"
- "run tests"
- "check worker health"
- "display elder settings"

Press `Ctrl+Shift+N` and type naturally!

### 📊 Sidebar Integration

The CodeFlow sidebar provides three views:

1. **Commands**: Browse all available commands by category
2. **System Status**: Real-time monitoring of workers and queues
3. **History**: Track your command execution history

Access the sidebar by clicking the robot icon in the Activity Bar.

### 📈 Status Bar

The status bar shows:
- Number of running workers
- Total message count in queues
- System health indicator (color-coded)

Click the status for detailed information.

### ⚡ Quick Command Execution

Execute commands in multiple ways:
- Command Palette (`Ctrl+Shift+P`)
- Keyboard shortcuts
- Sidebar click
- Natural language input

## Commands

### Core Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| Show AI Commands | Display all available commands | `Ctrl+Shift+A` |
| Natural Language Command | Use natural language to find commands | `Ctrl+Shift+N` |
| Show System Status | Display system health and status | `Ctrl+Shift+S` |
| Execute AI Command | Run a specific command | - |
| Open Settings | Configure extension settings | - |

### Command Categories

- **Core**: Basic system commands (start, stop, status, env)
- **Elder**: Elder management functions
- **Worker**: Worker management
- **Dev**: Development tools
- **Test**: Testing tools
- **Ops**: Operations
- **Monitor**: Monitoring and logs
- **Integrate**: External integrations

## Keyboard Shortcuts

### Windows/Linux

| Shortcut | Action |
|----------|---------|
| `Ctrl+Shift+A` | Show AI Commands |
| `Ctrl+Shift+N` | Natural Language Command |
| `Ctrl+Shift+S` | Show System Status |

### macOS

| Shortcut | Action |
|----------|---------|
| `Cmd+Shift+A` | Show AI Commands |
| `Cmd+Shift+N` | Natural Language Command |
| `Cmd+Shift+S` | Show System Status |

### Customizing Shortcuts

1. Open Keyboard Shortcuts: `Ctrl+K Ctrl+S`
2. Search for "CodeFlow"
3. Click the pencil icon to edit
4. Press your desired key combination

## Configuration

### Extension Settings

Access settings: `File → Preferences → Settings` → Search "CodeFlow"

| Setting | Description | Default |
|---------|-------------|---------|
| `codeflow.aiSystemPath` | Path to AI Command System | `/home/aicompany/ai_co/scripts/ai` |
| `codeflow.autoRefresh` | Auto-refresh system status | `true` |
| `codeflow.refreshInterval` | Refresh interval (seconds) | `30` |
| `codeflow.showNotifications` | Show execution notifications | `true` |
| `codeflow.enableNaturalLanguage` | Enable natural language processing | `true` |
| `codeflow.commandTimeout` | Command timeout (seconds) | `30` |

### Example Configuration

```json
{
  "codeflow.aiSystemPath": "/custom/path/to/ai",
  "codeflow.autoRefresh": true,
  "codeflow.refreshInterval": 60,
  "codeflow.showNotifications": false,
  "codeflow.commandTimeout": 45
}
```

## Troubleshooting

### Extension Not Loading Commands

1. **Check AI System Path**
   - Verify the path in settings is correct
   - Ensure the AI system is installed

2. **Check Permissions**
   - Ensure you have execute permissions for the AI system
   - Try running the AI system manually

3. **Reload Window**
   - Press `Ctrl+Shift+P` → "Developer: Reload Window"

### Commands Timing Out

1. **Increase Timeout**
   - Go to settings
   - Increase `codeflow.commandTimeout`

2. **Check System Load**
   - Verify the AI system is not overloaded
   - Check system resources

### Natural Language Not Working

1. **Check Setting**
   - Ensure `codeflow.enableNaturalLanguage` is `true`

2. **Verify AI System**
   - The AI system must support natural language processing
   - Check for any error messages

### Status Bar Not Updating

1. **Check Auto-refresh**
   - Ensure `codeflow.autoRefresh` is `true`

2. **Manual Refresh**
   - Click the refresh button in the sidebar

## FAQ

### Q: How do I update the extension?

A: VS Code will automatically notify you of updates. You can also check manually in the Extensions view.

### Q: Can I use custom commands?

A: Yes! Any commands available in your AI system will appear in CodeFlow.

### Q: How do I report issues?

A: Please report issues on our [GitHub repository](https://github.com/aicompany/codeflow/issues).

### Q: Is my data secure?

A: CodeFlow only communicates with your local AI system. No data is sent to external servers.

### Q: Can I contribute to the project?

A: Absolutely! Check our [Contributing Guide](https://github.com/aicompany/codeflow/blob/main/CONTRIBUTING.md).

### Q: How do I get support?

A:
- GitHub Issues for bug reports
- Discussions for questions
- Email: support@aicompany.dev

## Tips and Tricks

### 💡 Pro Tips

1. **Use Natural Language**
   - Don't memorize commands
   - Just describe what you want to do

2. **Customize Shortcuts**
   - Set up shortcuts for your most-used commands
   - Create a personalized workflow

3. **Monitor System Health**
   - Keep an eye on the status bar
   - Set up appropriate refresh intervals

4. **Review History**
   - Learn from your command patterns
   - Quickly re-run previous commands

### 🚀 Advanced Usage

1. **Command Chaining**
   - Execute multiple commands in sequence
   - Build complex workflows

2. **Integration with Tasks**
   - Create VS Code tasks that use CodeFlow commands
   - Automate your development workflow

3. **Workspace Settings**
   - Configure per-project settings
   - Share configurations with your team

## Updates and Changelog

See [CHANGELOG.md](https://github.com/aicompany/codeflow/blob/main/CHANGELOG.md) for version history and updates.

---

Thank you for using Elders Guild CodeFlow! We're constantly improving the extension based on your feedback. Happy coding! 🚀
