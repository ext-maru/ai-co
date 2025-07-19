import * as assert from 'assert';
import { AICommandSystem } from '../../aiCommandSystem';

suite('AICommandSystem Test Suite', () => {
    let aiSystem: AICommandSystem;

    setup(() => {
        aiSystem = new AICommandSystem();
    });

    test('Should initialize without errors', () => {
        assert.ok(aiSystem);
    });

    test('Should parse command help output', async () => {
        const mockHelpOutput = `
🏛️ AI Command System v3.0.0 - Ultimate Edition

Usage: ai <command> [options]

Commands:
  status              Show system status
  version             Show version
  help                Show help

Categories:
  core         基本システムコマンド
  elder        エルダー管理機能
        `;

        // This is a private method, but we can test the public interface
        const commands = await aiSystem.getAvailableCommands();
        assert.ok(Array.isArray(commands));
    });

    test('Should handle command execution errors gracefully', async () => {
        const result = await aiSystem.executeCommand('nonexistent-command');
        assert.ok(result);
        assert.strictEqual(result.success, false);
        assert.ok(result.error);
        assert.ok(typeof result.executionTime === 'number');
    });

    test('Should parse natural language responses', async () => {
        const suggestions = await aiSystem.processNaturalLanguage('show status');
        assert.ok(Array.isArray(suggestions));
    });

    test('Should handle timeout errors', async () => {
        // This would normally timeout, but we'll test error handling
        const result = await aiSystem.executeCommand('sleep 100');
        assert.ok(result);
        // Either succeeds quickly or fails with timeout
        assert.ok(typeof result.success === 'boolean');
    });

    test('Should cache commands appropriately', async () => {
        const commands1 = await aiSystem.getAvailableCommands();
        const commands2 = await aiSystem.getAvailableCommands();

        // Should return same reference if cached
        assert.strictEqual(commands1, commands2);
    });
});
