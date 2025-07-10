import * as vscode from 'vscode';
import { AICommandSystem } from './aiCommandSystem';

export interface CommandHistoryItem {
    command: string;
    timestamp: Date;
    success: boolean;
    executionTime: number;
}

export class HistoryProvider implements vscode.TreeDataProvider<HistoryItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<HistoryItem | undefined | null | void> = new vscode.EventEmitter<HistoryItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<HistoryItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private history: CommandHistoryItem[] = [];
    private maxHistorySize = 100;

    constructor(private aiSystem: AICommandSystem) {
        this.loadHistory();
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: HistoryItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: HistoryItem): Promise<HistoryItem[]> {
        if (!element) {
            if (this.history.length === 0) {
                return [new HistoryItem('No command history', '', vscode.TreeItemCollapsibleState.None)];
            }

            return this.history.slice(-20).reverse().map(item => {
                const icon = item.success ? '✅' : '❌';
                const timeStr = item.timestamp.toLocaleTimeString();
                const label = `${icon} ${item.command}`;
                const description = `${timeStr} (${item.executionTime}ms)`;
                
                const historyItem = new HistoryItem(label, description, vscode.TreeItemCollapsibleState.None);
                historyItem.command = {
                    command: 'codeflow.executeCommand',
                    title: 'Execute Command',
                    arguments: [item.command]
                };
                historyItem.contextValue = 'historyItem';
                return historyItem;
            });
        }

        return [];
    }

    addToHistory(command: string, success: boolean, executionTime: number): void {
        const item: CommandHistoryItem = {
            command,
            timestamp: new Date(),
            success,
            executionTime
        };

        this.history.push(item);
        
        // Keep only recent items
        if (this.history.length > this.maxHistorySize) {
            this.history = this.history.slice(-this.maxHistorySize);
        }

        this.saveHistory();
        this.refresh();
    }

    clearHistory(): void {
        this.history = [];
        this.saveHistory();
        this.refresh();
    }

    private loadHistory(): void {
        try {
            const saved = vscode.workspace.getConfiguration('codeflow').get<string>('commandHistory', '[]');
            const parsed = JSON.parse(saved);
            
            this.history = parsed.map((item: any) => ({
                command: item.command,
                timestamp: new Date(item.timestamp),
                success: item.success,
                executionTime: item.executionTime
            }));
        } catch (error) {
            console.error('Error loading command history:', error);
            this.history = [];
        }
    }

    private saveHistory(): void {
        try {
            const serialized = JSON.stringify(this.history.slice(-this.maxHistorySize));
            vscode.workspace.getConfiguration('codeflow').update('commandHistory', serialized, vscode.ConfigurationTarget.Global);
        } catch (error) {
            console.error('Error saving command history:', error);
        }
    }
}

export class HistoryItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly description: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = description;
        this.description = description;
        this.iconPath = new vscode.ThemeIcon('history');
    }
}