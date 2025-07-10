# Elders Guild CodeFlow - VS Code Extension

Elders Guild CodeFlow is a Visual Studio Code extension that integrates the powerful AI Command System directly into your development environment.

## Features

### 🚀 Core Features

- **Command Palette Integration**: Execute AI commands directly from VS Code
- **Natural Language Processing**: Use natural language to find and execute commands
- **Real-time System Status**: Monitor system health and worker status
- **Command History**: Track your command execution history
- **Sidebar Integration**: Dedicated sidebar with organized command categories

### 🎯 Key Capabilities

- **AI-Powered Command Discovery**: Find commands using natural language queries
- **System Monitoring**: Real-time status of workers, queues, and system health
- **Quick Command Execution**: Execute commands with keyboard shortcuts
- **Auto-refresh**: Automatically update system status
- **Customizable Settings**: Configure paths, timeouts, and notification preferences

## Installation

### Prerequisites

- Visual Studio Code 1.74.0 or higher
- Elders Guild system installed and accessible
- Node.js 16.x or higher (for development)

### Install from VSIX

1. Download the latest `.vsix` file from releases
2. Open VS Code
3. Go to Extensions (Ctrl+Shift+X)
4. Click "..." menu and select "Install from VSIX..."
5. Select the downloaded file

### Install from Marketplace

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Elders Guild CodeFlow"
4. Click "Install"

## Usage

### Keyboard Shortcuts

- `Ctrl+Shift+A` (`Cmd+Shift+A` on Mac): Show AI Commands
- `Ctrl+Shift+N` (`Cmd+Shift+N` on Mac): Natural Language Command
- `Ctrl+Shift+S` (`Cmd+Shift+S` on Mac): Show System Status

### Command Palette

Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and type:

- `CodeFlow: Show AI Commands`
- `CodeFlow: Execute AI Command`
- `CodeFlow: Show System Status`
- `CodeFlow: Natural Language Command`
- `CodeFlow: Show Elder Settings`

### Sidebar

The CodeFlow sidebar provides:

- **Commands**: Organized by category for easy discovery
- **System Status**: Real-time monitoring of workers and queues
- **Command History**: Recent command execution history

### Natural Language Commands

Use natural language to find commands:

1. Press `Ctrl+Shift+N` (or use Command Palette)
2. Type what you want to do:
   - "show system status"
   - "run tests"
   - "check worker health"
   - "display elder settings"
3. Select from AI-suggested commands

## Configuration

### Settings

Open VS Code settings (`Ctrl+,` / `Cmd+,`) and search for "CodeFlow":

- **AI System Path**: Path to AI Command System executable
- **Auto Refresh**: Enable automatic status updates
- **Refresh Interval**: How often to refresh status (seconds)
- **Show Notifications**: Display command execution notifications
- **Enable Natural Language**: Enable AI natural language processing
- **Command Timeout**: Maximum execution time for commands (seconds)

### Example Settings

```json
{
  "codeflow.aiSystemPath": "/home/aicompany/ai_co/scripts/ai",
  "codeflow.autoRefresh": true,
  "codeflow.refreshInterval": 30,
  "codeflow.showNotifications": true,
  "codeflow.enableNaturalLanguage": true,
  "codeflow.commandTimeout": 30
}
```

## Development

### Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Open in VS Code
4. Press `F5` to start debugging

### Building

```bash
npm run compile
```

### Testing

```bash
npm run test
```

### Packaging

```bash
npm run package
```

## Architecture

### Components

- **Extension**: Main extension entry point
- **AICommandSystem**: Core communication with AI system
- **CommandProvider**: Tree view provider for commands
- **StatusProvider**: Tree view provider for system status
- **HistoryProvider**: Tree view provider for command history

### Data Flow

1. Extension activates and initializes providers
2. Providers communicate with AICommandSystem
3. AICommandSystem executes shell commands to AI system
4. Results are parsed and displayed in VS Code UI

## Troubleshooting

### Common Issues

**Extension not loading commands**
- Check AI System Path in settings
- Ensure AI system is installed and accessible
- Verify permissions for the AI system executable

**Commands failing to execute**
- Increase command timeout in settings
- Check AI system logs for errors
- Verify system dependencies are installed

**Natural language not working**
- Ensure "Enable Natural Language" is enabled in settings
- Check AI system supports natural language processing
- Verify AI system is running and accessible

### Debug Mode

1. Open VS Code Developer Console (`Help > Toggle Developer Tools`)
2. Look for CodeFlow extension logs
3. Check for error messages or warnings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- GitHub Issues: [Report issues](https://github.com/aicompany/codeflow/issues)
- Documentation: [Wiki](https://github.com/aicompany/codeflow/wiki)
- Elders Guild: [Main Project](https://github.com/aicompany/ai_co)

## Changelog

### 1.0.0

- Initial release
- Command palette integration
- Natural language processing
- System status monitoring
- Command history tracking
- Sidebar integration
- Keyboard shortcuts
- Customizable settings

---

**Elders Guild CodeFlow** - Bringing AI-powered development tools directly to your IDE.

🚀 Built with ❤️ by the Elders Guild team