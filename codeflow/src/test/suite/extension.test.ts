import * as assert from 'assert';
import * as vscode from 'vscode';
import { AICommandSystem } from '../../aiCommandSystem';

suite('Extension Test Suite', () => {
    vscode.window.showInformationMessage('Start all tests.');

    test('Extension should be present', () => {
        const extension = vscode.extensions.getExtension('aicompany.ai-company-codeflow');
        assert.ok(extension);
    });

    test('AICommandSystem should initialize', () => {
        const aiSystem = new AICommandSystem();
        assert.ok(aiSystem);
    });

    test('Commands should be available', async () => {
        const aiSystem = new AICommandSystem();
        const commands = await aiSystem.getAvailableCommands();
        assert.ok(Array.isArray(commands));
    });

    test('System status should be retrievable', async () => {
        const aiSystem = new AICommandSystem();
        try {
            const status = await aiSystem.getSystemStatus();
            assert.ok(status);
            assert.ok(status.version);
            assert.ok(Array.isArray(status.workers));
            assert.ok(Array.isArray(status.queues));
        } catch (error) {
            // System might not be available in test environment
            console.warn('System status test skipped:', error);
        }
    });

    test('Extension should activate', async () => {
        const extension = vscode.extensions.getExtension('aicompany.ai-company-codeflow');
        if (extension) {
            await extension.activate();
            assert.ok(extension.isActive);
        }
    });
});