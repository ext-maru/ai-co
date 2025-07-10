import * as vscode from 'vscode';
import { AICommandSystem } from './aiCommandSystem';

export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;
    private refreshInterval: NodeJS.Timer | undefined;
    private isActive: boolean = false;

    constructor(private aiSystem: AICommandSystem) {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        
        this.statusBarItem.command = 'codeflow.showStatus';
        this.statusBarItem.tooltip = 'Click to show AI system status';
        
        this.initialize();
    }

    private async initialize(): Promise<void> {
        await this.updateStatus();
        this.statusBarItem.show();
        this.startAutoRefresh();
    }

    private async updateStatus(): Promise<void> {
        try {
            const status = await this.aiSystem.getSystemStatus();
            const runningWorkers = status.workers.filter(w => w.status === 'Running').length;
            const totalWorkers = status.workers.length;
            const totalMessages = status.queues.reduce((sum, q) => sum + q.messages, 0);
            
            // Create status text
            const statusText = `AI: ${runningWorkers}/${totalWorkers} workers`;
            const messageText = totalMessages > 0 ? ` (${totalMessages} msgs)` : '';
            
            this.statusBarItem.text = `$(robot) ${statusText}${messageText}`;
            
            // Set color based on system health
            if (runningWorkers === 0) {
                this.statusBarItem.color = new vscode.ThemeColor('statusBarItem.errorForeground');
            } else if (runningWorkers < totalWorkers) {
                this.statusBarItem.color = new vscode.ThemeColor('statusBarItem.warningForeground');
            } else {
                this.statusBarItem.color = undefined; // Use default color
            }
            
        } catch (error) {
            this.statusBarItem.text = '$(robot) AI: Offline';
            this.statusBarItem.color = new vscode.ThemeColor('statusBarItem.errorForeground');
            console.error('Error updating status bar:', error);
        }
    }

    private startAutoRefresh(): void {
        const config = vscode.workspace.getConfiguration('codeflow');
        const autoRefresh = config.get<boolean>('autoRefresh', true);
        const refreshInterval = config.get<number>('refreshInterval', 30) * 1000;
        
        if (autoRefresh && !this.refreshInterval) {
            this.refreshInterval = setInterval(() => {
                this.updateStatus();
            }, refreshInterval);
        }
    }

    private stopAutoRefresh(): void {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = undefined;
        }
    }

    public refresh(): void {
        this.updateStatus();
    }

    public show(): void {
        this.statusBarItem.show();
        this.isActive = true;
    }

    public hide(): void {
        this.statusBarItem.hide();
        this.isActive = false;
    }

    public dispose(): void {
        this.stopAutoRefresh();
        this.statusBarItem.dispose();
    }

    public updateConfiguration(): void {
        this.stopAutoRefresh();
        this.startAutoRefresh();
    }
}