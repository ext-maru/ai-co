import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface Command {
    name: string;
    description: string;
    category: string;
    permission?: string;
}

export interface CommandResult {
    success: boolean;
    output: string;
    error?: string;
    executionTime: number;
}

export interface SystemStatus {
    version: string;
    uptime: string;
    workers: Array<{
        name: string;
        status: string;
        lastActivity: string;
    }>;
    queues: Array<{
        name: string;
        messages: number;
    }>;
    permissions: string;
}

export interface NaturalLanguageSuggestion {
    command: string;
    confidence: number;
    reason: string;
}

export class AICommandSystem {
    private aiSystemPath: string;
    private commandCache: Command[] = [];
    private lastCacheUpdate: number = 0;
    private readonly cacheTimeout = 60000; // 1 minute

    constructor() {
        const config = vscode.workspace.getConfiguration('codeflow');
        this.aiSystemPath = config.get<string>('aiSystemPath', '/home/aicompany/ai_co/scripts/ai');
    }

    async getAvailableCommands(): Promise<Command[]> {
        const now = Date.now();
        if (this.commandCache.length > 0 && (now - this.lastCacheUpdate) < this.cacheTimeout) {
            return this.commandCache;
        }

        try {
            const result = await this.executeAICommand('help');
            if (result.output && !result.error) {
                this.commandCache = this.parseCommandsFromHelp(result.output);
                this.lastCacheUpdate = now;
                return this.commandCache;
            }
        } catch (error) {
            console.error('Error getting available commands:', error);
        }

        return [];
    }

    async executeCommand(command: string): Promise<CommandResult> {
        const config = vscode.workspace.getConfiguration('codeflow');
        const timeout = config.get<number>('commandTimeout', 30) * 1000;
        
        const startTime = Date.now();
        
        try {
            const result = await this.executeAICommand(command, timeout);
            const executionTime = Date.now() - startTime;
            
            return {
                success: true,
                output: result.output,
                executionTime
            };
        } catch (error) {
            const executionTime = Date.now() - startTime;
            
            return {
                success: false,
                output: '',
                error: error instanceof Error ? error.message : String(error),
                executionTime
            };
        }
    }

    async getSystemStatus(): Promise<SystemStatus> {
        try {
            const [statusResult, versionResult] = await Promise.all([
                this.executeAICommand('status'),
                this.executeAICommand('version')
            ]);

            const status = this.parseStatusOutput(statusResult.output);
            const version = this.parseVersionOutput(versionResult.output);

            return {
                version,
                uptime: 'N/A',
                workers: status.workers,
                queues: status.queues,
                permissions: status.permissions
            };
        } catch (error) {
            throw new Error(`Failed to get system status: ${error}`);
        }
    }

    async processNaturalLanguage(input: string): Promise<NaturalLanguageSuggestion[]> {
        const config = vscode.workspace.getConfiguration('codeflow');
        const enableNaturalLanguage = config.get<boolean>('enableNaturalLanguage', true);
        
        if (!enableNaturalLanguage) {
            return [];
        }

        try {
            const result = await this.executeAICommand(`ask "${input}"`);
            if (result.output && !result.error) {
                return this.parseNaturalLanguageResponse(result.output);
            }
        } catch (error) {
            console.error('Error processing natural language:', error);
        }

        return [];
    }

    private async executeAICommand(command: string, timeout: number = 30000): Promise<{ output: string; error?: string }> {
        const fullCommand = `${this.aiSystemPath} ${command}`;
        
        try {
            const { stdout, stderr } = await execAsync(fullCommand, { timeout });
            return { output: stdout, error: stderr };
        } catch (error: any) {
            if (error.code === 'TIMEOUT') {
                throw new Error('Command execution timed out');
            }
            throw error;
        }
    }

    private parseCommandsFromHelp(helpOutput: string): Command[] {
        const commands: Command[] = [];
        const lines = helpOutput.split('\n');
        
        let currentCategory = '';
        let inCommandsSection = false;
        
        for (const line of lines) {
            const trimmed = line.trim();
            
            // Detect category headers
            if (trimmed.endsWith(':') && !trimmed.startsWith(' ')) {
                currentCategory = trimmed.slice(0, -1);
                inCommandsSection = true;
                continue;
            }
            
            // Parse command lines
            if (inCommandsSection && trimmed.startsWith(' ') && trimmed.includes(' ')) {
                const parts = trimmed.split(/\s+/);
                if (parts.length >= 2) {
                    const name = parts[0];
                    const description = parts.slice(1).join(' ');
                    
                    commands.push({
                        name,
                        description,
                        category: currentCategory
                    });
                }
            }
            
            // Reset when we hit a new section
            if (trimmed === '' || (!trimmed.startsWith(' ') && !trimmed.endsWith(':'))) {
                inCommandsSection = false;
            }
        }
        
        return commands;
    }

    private parseStatusOutput(statusOutput: string): {
        workers: Array<{ name: string; status: string; lastActivity: string }>;
        queues: Array<{ name: string; messages: number }>;
        permissions: string;
    } {
        const workers: Array<{ name: string; status: string; lastActivity: string }> = [];
        const queues: Array<{ name: string; messages: number }> = [];
        let permissions = 'Unknown';

        const lines = statusOutput.split('\n');
        
        for (const line of lines) {
            const trimmed = line.trim();
            
            // Parse worker status
            if (trimmed.includes('Worker') && (trimmed.includes('✅') || trimmed.includes('❌'))) {
                const status = trimmed.includes('✅') ? 'Running' : 'Stopped';
                const match = trimmed.match(/(\w+Worker)/);
                if (match) {
                    workers.push({
                        name: match[1],
                        status,
                        lastActivity: 'N/A'
                    });
                }
            }
            
            // Parse queue status
            if (trimmed.includes('queue:') && trimmed.includes('messages')) {
                const queueMatch = trimmed.match(/(\w+)\s+queue:\s+(\d+)\s+messages/);
                if (queueMatch) {
                    queues.push({
                        name: queueMatch[1],
                        messages: parseInt(queueMatch[2])
                    });
                }
            }
            
            // Parse permissions
            if (trimmed.includes('Permission Level:')) {
                const permMatch = trimmed.match(/Permission Level:\s+(\w+)/);
                if (permMatch) {
                    permissions = permMatch[1];
                }
            }
        }

        return { workers, queues, permissions };
    }

    private parseVersionOutput(versionOutput: string): string {
        const lines = versionOutput.split('\n');
        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('AI Command System')) {
                const match = trimmed.match(/v(\d+\.\d+\.\d+)/);
                if (match) {
                    return match[1];
                }
            }
        }
        return 'Unknown';
    }

    private parseNaturalLanguageResponse(response: string): NaturalLanguageSuggestion[] {
        const suggestions: NaturalLanguageSuggestion[] = [];
        const lines = response.split('\n');
        
        for (const line of lines) {
            const trimmed = line.trim();
            
            // Look for numbered suggestions
            const match = trimmed.match(/^\s*(\d+)\.\s*(.+?)\s*\((\d+)%\)/);
            if (match) {
                const command = match[2];
                const confidence = parseInt(match[3]);
                
                suggestions.push({
                    command,
                    confidence,
                    reason: 'Natural language analysis'
                });
            }
        }
        
        return suggestions;
    }
}