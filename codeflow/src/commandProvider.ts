import * as vscode from 'vscode';
import { AICommandSystem, Command } from './aiCommandSystem';

export class CommandProvider implements vscode.TreeDataProvider<CommandItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<CommandItem | undefined | null | void> = new vscode.EventEmitter<CommandItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<CommandItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private commands: Command[] = [];
    private loading: boolean = false;

    constructor(private aiSystem: AICommandSystem) {
        this.loadCommands();
    }

    refresh(): void {
        this.loadCommands();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: CommandItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: CommandItem): Promise<CommandItem[]> {
        if (this.loading) {
            return [new CommandItem('Loading...', '', vscode.TreeItemCollapsibleState.None)];
        }

        if (!element) {
            // Return categories
            const categories = [...new Set(this.commands.map(cmd => cmd.category))];
            return categories.map(category => 
                new CommandItem(category, '', vscode.TreeItemCollapsibleState.Expanded, true)
            );
        }

        if (element.isCategory) {
            // Return commands in category
            const categoryCommands = this.commands.filter(cmd => cmd.category === element.label);
            return categoryCommands.map(cmd => {
                const item = new CommandItem(cmd.name, cmd.description, vscode.TreeItemCollapsibleState.None);
                item.command = {
                    command: 'codeflow.executeCommand',
                    title: 'Execute Command',
                    arguments: [cmd.name]
                };
                item.contextValue = 'command';
                return item;
            });
        }

        return [];
    }

    private async loadCommands(): Promise<void> {
        this.loading = true;
        try {
            this.commands = await this.aiSystem.getAvailableCommands();
        } catch (error) {
            console.error('Error loading commands:', error);
            vscode.window.showErrorMessage('Failed to load AI commands');
        } finally {
            this.loading = false;
        }
    }
}

export class CommandItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly description: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly isCategory: boolean = false
    ) {
        super(label, collapsibleState);
        this.tooltip = description;
        this.description = description;
        
        if (isCategory) {
            this.iconPath = new vscode.ThemeIcon('folder');
        } else {
            this.iconPath = new vscode.ThemeIcon('terminal');
        }
    }
}