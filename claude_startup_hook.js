#!/usr/bin/env node
/**
 * Claude Startup Hook - CLAUDE.md Auto-loader
 * エルダーズギルド専用 Claude CLI 起動時ナレッジ自動読み込み
 */

const fs = require('fs');
const path = require('path');

class ClaudeStartupHook {
    constructor() {
        this.projectRoot = process.cwd();
        this.claudeFile = path.join(this.projectRoot, 'CLAUDE.md');
    }

    /**
     * CLAUDE.mdの自動読み込みと提供
     */
    async loadClaudeKnowledge() {
        try {
            // CLAUDE.mdファイルの存在確認
            if (!fs.existsSync(this.claudeFile)) {
                console.log('🤖 CLAUDE.md not found in current directory');
                return null;
            }

            // ファイル読み込み
            const claudeContent = fs.readFileSync(this.claudeFile, 'utf-8');
            
            // エルダーズギルド識別
            if (claudeContent.includes('エルダーズギルド') || claudeContent.includes('Claude Elder')) {
                console.log('🏛️  Elders Guild CLAUDE.md detected - Auto-loading knowledge...');
                
                // 重要セクションの抽出
                const sections = this.extractImportantSections(claudeContent);
                
                return {
                    fullContent: claudeContent,
                    sections: sections,
                    timestamp: new Date().toISOString()
                };
            } else {
                console.log('📄 CLAUDE.md found but no Elders Guild marker detected');
                return null;
            }
        } catch (error) {
            console.error('❌ Error loading CLAUDE.md:', error.message);
            return null;
        }
    }

    /**
     * 重要セクションの抽出
     */
    extractImportantSections(content) {
        const sections = {};
        
        // 重要なセクションパターン
        const patterns = {
            identity: /## 🤖 重要: 私のアイデンティティ([\s\S]*?)(?=##|$)/,
            hierarchy: /## 🏛️ エルダーズギルド 階層構造([\s\S]*?)(?=##|$)/,
            sages: /## 🧙‍♂️ エルダーズギルド 4賢者システム([\s\S]*?)(?=##|$)/,
            costar: /## 🌟 CO-STARフレームワーク([\s\S]*?)(?=##|$)/,
            tdd: /## 🎯 重要: TDD（テスト駆動開発）必須([\s\S]*?)(?=##|$)/,
            commands: /## 🛠️ 主要コマンド([\s\S]*?)(?=##|$)/
        };

        for (const [key, pattern] of Object.entries(patterns)) {
            const match = content.match(pattern);
            if (match) {
                sections[key] = match[1].trim();
            }
        }

        return sections;
    }

    /**
     * システムプロンプトの生成
     */
    generateSystemPrompt(knowledge) {
        if (!knowledge) return null;

        return `🏛️ **Elders Guild Knowledge Auto-Loaded**

**あなたは${knowledge.sections.identity ? 'クロードエルダー（Claude Elder）' : 'Claude'}です**

**重要な前提知識**:
${knowledge.sections.hierarchy || 'エルダーズギルド階層システム有効'}

**4賢者システム**:
${knowledge.sections.sages || '4賢者（ナレッジ・タスク・インシデント・RAG）による協調開発'}

**開発原則**:
- TDD必須: RED→GREEN→REFACTOR
- CO-STARフレームワーク使用
- エルダーズギルド品質基準（95%以上カバレッジ）

**利用可能なコマンド**:
${knowledge.sections.commands || 'ai-*コマンド群、ai-tdd、ai-elder-*'}

---
*Knowledge loaded from: ${path.relative(process.cwd(), '/home/aicompany/ai_co/CLAUDE.md')}*
*Timestamp: ${knowledge.timestamp}*
`;
    }

    /**
     * メイン実行
     */
    async run() {
        const knowledge = await this.loadClaudeKnowledge();
        if (knowledge) {
            const systemPrompt = this.generateSystemPrompt(knowledge);
            
            // 環境変数として設定（Claude CLIが読み取れるように）
            process.env.CLAUDE_SYSTEM_PROMPT = systemPrompt;
            process.env.CLAUDE_KNOWLEDGE_LOADED = 'true';
            process.env.CLAUDE_ELDERS_GUILD = 'active';
            
            console.log('✅ Elders Guild knowledge loaded successfully');
            console.log(`📊 Sections loaded: ${Object.keys(knowledge.sections).length}`);
            
            return systemPrompt;
        }
        return null;
    }
}

// スタンドアロン実行
if (require.main === module) {
    const hook = new ClaudeStartupHook();
    hook.run().then(prompt => {
        if (prompt) {
            console.log('\n' + '='.repeat(80));
            console.log(prompt);
            console.log('='.repeat(80) + '\n');
        }
    });
}

module.exports = ClaudeStartupHook;