import * as vscode from 'vscode';
import { AICommandSystem } from './aiCommandSystem';
import { CommandProvider } from './commandProvider';
import { StatusProvider } from './statusProvider';
import { HistoryProvider } from './historyProvider';
import { StatusBarManager } from './statusBar';

export function activate(context: vscode.ExtensionContext) {
    console.log('AI Company CodeFlow extension is now active!');

    // Initialize AI Command System
    const aiSystem = new AICommandSystem();

    // Initialize providers
    const commandProvider = new CommandProvider(aiSystem);
    const statusProvider = new StatusProvider(aiSystem);
    const historyProvider = new HistoryProvider(aiSystem);
    const statusBarManager = new StatusBarManager(aiSystem);

    // Register tree data providers
    vscode.window.registerTreeDataProvider('codeflow.commands', commandProvider);
    vscode.window.registerTreeDataProvider('codeflow.status', statusProvider);
    vscode.window.registerTreeDataProvider('codeflow.history', historyProvider);

    // Register commands
    const commands = [
        vscode.commands.registerCommand('codeflow.showCommands', () => {
            showCommandQuickPick(aiSystem);
        }),

        vscode.commands.registerCommand('codeflow.executeCommand', (command?: string) => {
            if (command) {
                executeCommand(aiSystem, command);
            } else {
                showCommandQuickPick(aiSystem);
            }
        }),

        vscode.commands.registerCommand('codeflow.showStatus', () => {
            showSystemStatus(aiSystem);
        }),

        vscode.commands.registerCommand('codeflow.openSettings', () => {
            vscode.commands.executeCommand('workbench.action.openSettings', 'codeflow');
        }),

        vscode.commands.registerCommand('codeflow.naturalLanguage', () => {
            showNaturalLanguageInput(aiSystem);
        }),

        vscode.commands.registerCommand('codeflow.showElderSettings', () => {
            executeCommand(aiSystem, 'elder settings');
        }),

        vscode.commands.registerCommand('codeflow.refreshCommands', () => {
            commandProvider.refresh();
        }),

        vscode.commands.registerCommand('codeflow.refreshStatus', () => {
            statusProvider.refresh();
        }),

        vscode.commands.registerCommand('codeflow.refreshHistory', () => {
            historyProvider.refresh();
        })
    ];

    // Add commands to context subscriptions
    context.subscriptions.push(...commands);
    context.subscriptions.push(statusBarManager);

    // Setup auto-refresh
    setupAutoRefresh(statusProvider);

    // Show welcome message
    vscode.window.showInformationMessage('AI Company CodeFlow activated! 🚀');
}

async function showCommandQuickPick(aiSystem: AICommandSystem) {
    const commands = await aiSystem.getAvailableCommands();

    const items = commands.map(cmd => ({
        label: cmd.name,
        description: cmd.description,
        detail: cmd.category
    }));

    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'Select a command to execute',
        matchOnDescription: true,
        matchOnDetail: true
    });

    if (selected) {
        executeCommand(aiSystem, selected.label);
    }
}

async function executeCommand(aiSystem: AICommandSystem, command: string) {
    const config = vscode.workspace.getConfiguration('codeflow');
    const showNotifications = config.get<boolean>('showNotifications', true);

    if (showNotifications) {
        vscode.window.showInformationMessage(`Executing: ${command}`);
    }

    try {
        const result = await aiSystem.executeCommand(command);

        if (result.success) {
            if (showNotifications) {
                vscode.window.showInformationMessage(`Command completed successfully`);
            }

            // Show output in new document
            const doc = await vscode.workspace.openTextDocument({
                content: result.output,
                language: 'plaintext'
            });

            await vscode.window.showTextDocument(doc);
        } else {
            vscode.window.showErrorMessage(`Command failed: ${result.error}`);
        }
    } catch (error) {
        vscode.window.showErrorMessage(`Error executing command: ${error}`);
    }
}

async function showSystemStatus(aiSystem: AICommandSystem) {
    try {
        const status = await aiSystem.getSystemStatus();

        const doc = await vscode.workspace.openTextDocument({
            content: JSON.stringify(status, null, 2),
            language: 'json'
        });

        await vscode.window.showTextDocument(doc);
    } catch (error) {
        vscode.window.showErrorMessage(`Error getting system status: ${error}`);
    }
}

async function showNaturalLanguageInput(aiSystem: AICommandSystem) {
    const config = vscode.workspace.getConfiguration('codeflow');
    const enableNaturalLanguage = config.get<boolean>('enableNaturalLanguage', true);

    if (!enableNaturalLanguage) {
        vscode.window.showWarningMessage('Natural language processing is disabled in settings');
        return;
    }

    const input = await vscode.window.showInputBox({
        placeHolder: 'Describe what you want to do (e.g., "show system status", "run tests")',
        prompt: 'Enter natural language command'
    });

    if (input) {
        try {
            const suggestions = await aiSystem.processNaturalLanguage(input);

            if (suggestions.length === 0) {
                vscode.window.showWarningMessage('No matching commands found');
                return;
            }

            const items = suggestions.map(suggestion => ({
                label: suggestion.command,
                description: `${suggestion.confidence}% confidence`,
                detail: suggestion.reason
            }));

            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select the command you want to execute',
                matchOnDescription: true,
                matchOnDetail: true
            });

            if (selected) {
                executeCommand(aiSystem, selected.label);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Error processing natural language: ${error}`);
        }
    }
}

function setupAutoRefresh(statusProvider: StatusProvider) {
    const config = vscode.workspace.getConfiguration('codeflow');
    const autoRefresh = config.get<boolean>('autoRefresh', true);
    const refreshInterval = config.get<number>('refreshInterval', 30) * 1000;

    if (autoRefresh) {
        setInterval(() => {
            statusProvider.refresh();
        }, refreshInterval);
    }
}

export function deactivate() {
    console.log('AI Company CodeFlow extension is now deactivated');
}
