import * as vscode from 'vscode';
import { AICommandSystem, SystemStatus } from './aiCommandSystem';

export class StatusProvider implements vscode.TreeDataProvider<StatusItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<StatusItem | undefined | null | void> = new vscode.EventEmitter<StatusItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<StatusItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private systemStatus: SystemStatus | null = null;
    private loading: boolean = false;

    constructor(private aiSystem: AICommandSystem) {
        this.loadStatus();
    }

    refresh(): void {
        this.loadStatus();
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: StatusItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: StatusItem): Promise<StatusItem[]> {
        if (this.loading) {
            return [new StatusItem('Loading...', '', vscode.TreeItemCollapsibleState.None)];
        }

        if (!this.systemStatus) {
            return [new StatusItem('Failed to load status', '', vscode.TreeItemCollapsibleState.None)];
        }

        if (!element) {
            return [
                new StatusItem('System Info', '', vscode.TreeItemCollapsibleState.Expanded, 'info'),
                new StatusItem('Workers', '', vscode.TreeItemCollapsibleState.Expanded, 'workers'),
                new StatusItem('Queues', '', vscode.TreeItemCollapsibleState.Expanded, 'queues')
            ];
        }

        switch (element.contextValue) {
            case 'info':
                return [
                    new StatusItem(`Version: ${this.systemStatus.version}`, '', vscode.TreeItemCollapsibleState.None),
                    new StatusItem(`Permissions: ${this.systemStatus.permissions}`, '', vscode.TreeItemCollapsibleState.None),
                    new StatusItem(`Uptime: ${this.systemStatus.uptime}`, '', vscode.TreeItemCollapsibleState.None)
                ];

            case 'workers':
                return this.systemStatus.workers.map(worker => {
                    const icon = worker.status === 'Running' ? '✅' : '❌';
                    return new StatusItem(
                        `${icon} ${worker.name}`,
                        worker.status,
                        vscode.TreeItemCollapsibleState.None
                    );
                });

            case 'queues':
                return this.systemStatus.queues.map(queue => {
                    const icon = queue.messages > 0 ? '📬' : '📭';
                    return new StatusItem(
                        `${icon} ${queue.name}`,
                        `${queue.messages} messages`,
                        vscode.TreeItemCollapsibleState.None
                    );
                });

            default:
                return [];
        }
    }

    private async loadStatus(): Promise<void> {
        this.loading = true;
        try {
            this.systemStatus = await this.aiSystem.getSystemStatus();
        } catch (error) {
            console.error('Error loading system status:', error);
            vscode.window.showErrorMessage('Failed to load system status');
        } finally {
            this.loading = false;
        }
    }
}

export class StatusItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly description: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue?: string
    ) {
        super(label, collapsibleState);
        this.tooltip = description;
        this.description = description;
        
        if (contextValue) {
            this.contextValue = contextValue;
        }
        
        // Set icons based on context
        switch (contextValue) {
            case 'info':
                this.iconPath = new vscode.ThemeIcon('info');
                break;
            case 'workers':
                this.iconPath = new vscode.ThemeIcon('person');
                break;
            case 'queues':
                this.iconPath = new vscode.ThemeIcon('inbox');
                break;
            default:
                this.iconPath = new vscode.ThemeIcon('circle-filled');
        }
    }
}