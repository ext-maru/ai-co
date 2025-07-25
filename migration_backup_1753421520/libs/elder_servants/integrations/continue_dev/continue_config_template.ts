/**
 * Continue.dev Configuration Template for Elder Servants Integration
 * This file demonstrates how to configure Continue to use Elder Servants as custom assistants
 */

import { Config } from "@continuedev/config";

// Elder Servants endpoints configuration
const ELDER_SERVANTS_BASE_URL = process.env.ELDER_SERVANTS_URL || "http://localhost:8000";

// Custom Elder Servant Provider
class ElderServantProvider {
  constructor(
    private servantId: string,
    private baseUrl: string = ELDER_SERVANTS_BASE_URL
  ) {}

  async complete(prompt: string, options: any) {
    const response = await fetch(`${this.baseUrl}/elder/servants/${this.servantId}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "execute_task",
        task: {
          type: "code_generation",
          prompt: prompt,
          context: options.context || {}
        }
      })
    });

    const result = await response.json();
    return result.result.result_data.generated_code || "";
  }
}

export const config: Config = {
  // モデル設定
  models: [
    {
      title: "Elder Code Craftsman",
      provider: new ElderServantProvider("code-craftsman"),
      model: "elder-servant",
      apiKey: "elder-guild-key",
    },
    {
      title: "Elder Test Guardian",
      provider: new ElderServantProvider("test-guardian"),
      model: "elder-servant",
      apiKey: "elder-guild-key",
    },
    {
      title: "Elder Quality Inspector",
      provider: new ElderServantProvider("quality-inspector"),
      model: "elder-servant",
      apiKey: "elder-guild-key",
    }
  ],

  // カスタムコマンド（スラッシュコマンド）
  slashCommands: [
    {
      name: "elder-flow",
      description: "Execute Elder Flow for the current task",
      run: async function* (sdk) {
        yield "🌊 Initiating Elder Flow...";

        const response = await fetch(`${ELDER_SERVANTS_BASE_URL}/elder/flow/execute`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: sdk.input,
            context: {
              files: await sdk.ide.getOpenFiles(),
              workspace: await sdk.ide.getWorkspaceDirs()
            }
          })
        });

        const result = await response.json();
        yield `✅ Elder Flow completed: ${result.message}`;
      }
    },
    {
      name: "sage-consult",
      description: "Consult with the 4 Sages",
      run: async function* (sdk) {
        yield "🧙‍♂️ Consulting with the 4 Sages...";

        const response = await fetch(`${ELDER_SERVANTS_BASE_URL}/elder/sages/consult`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: sdk.input,
            context: {
              currentFile: await sdk.ide.getCurrentFile()
            }
          })
        });

        const wisdom = await response.json();
        yield `📜 Sage Wisdom:\n${wisdom.advice}`;
      }
    },
    {
      name: "iron-will-check",
      description: "Check code quality against Iron Will standards",
      run: async function* (sdk) {
        yield "🗡️ Checking Iron Will quality standards...";

        const currentFile = await sdk.ide.getCurrentFile();
        if (!currentFile) {
          yield "❌ No file selected";
          return;
        }

        const response = await fetch(`${ELDER_SERVANTS_BASE_URL}/elder/quality/iron-will`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            file_path: currentFile.path,
            content: currentFile.content
          })
        });

        const quality = await response.json();
        yield `${quality.score >= 95 ? "✅" : "❌"} Quality Score: ${quality.score}%\n${quality.details}`;
      }
    }
  ],

  // カスタムコンテキストプロバイダー
  contextProviders: [
    {
      title: "Elder Knowledge Base",
      getContextItems: async (query: string) => {
        const response = await fetch(`${ELDER_SERVANTS_BASE_URL}/elder/knowledge/search`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query })
        });

        const knowledge = await response.json();
        return knowledge.items.map((item: any) => ({
          name: item.title,
          description: item.summary,
          content: item.content
        }));
      }
    },
    {
      title: "Active Elder Tasks",
      getContextItems: async () => {
        const response = await fetch(`${ELDER_SERVANTS_BASE_URL}/elder/tasks/active`);
        const tasks = await response.json();

        return tasks.map((task: any) => ({
          name: `Task: ${task.name}`,
          description: `Priority: ${task.priority} | Status: ${task.status}`,
          content: JSON.stringify(task, null, 2)
        }));
      }
    }
  ],

  // 実験的機能
  experimental: {
    // Elder Servantの非同期実行を有効化
    asyncServantExecution: true,
    // 4賢者システムとの深い統合
    fourSagesIntegration: true,
    // Iron Will自動適用
    autoIronWillEnforcement: true
  },

  // タブオートコンプリート設定
  tabAutocompleteModel: {
    title: "Elder Code Craftsman (Fast)",
    provider: new ElderServantProvider("code-craftsman-fast"),
    model: "elder-servant-autocomplete"
  },

  // アシスタント設定
  systemMessage: `You are integrated with the Elder Guild system.
  You have access to:
  - 4 Sages (Knowledge, Task, Incident, RAG)
  - Elder Servants (Code Craftsman, Test Guardian, Quality Inspector, Git Keeper)
  - Elder Flow automation
  - Iron Will quality standards (95% minimum)

  Always maintain the highest quality standards and consult with the appropriate systems when needed.`,

  // 埋め込みプロバイダー（RAG用）
  embeddingsProvider: {
    provider: "elder-rag",
    model: "elder-embeddings",
    apiBase: `${ELDER_SERVANTS_BASE_URL}/elder/embeddings`
  }
};
