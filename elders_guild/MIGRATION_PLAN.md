# 新エルダーズギルド正規化計画

## 移行対象ファイル

### 1. 品質サーバント
**From**: `libs/quality/servants/`
**To**: `elders_guild/quality_servants/`
- quality_watcher_servant.py
- test_forge_servant.py
- comprehensive_guardian_servant.py

### 2. 品質システム
**From**: `libs/quality/`
**To**: `elders_guild/quality/`
- quality_pipeline_orchestrator.py
- static_analysis_engine.py
- test_automation_engine.py
- comprehensive_quality_engine.py

### 3. Elder CLI
**From**: プロジェクトルート
**To**: `elders_guild/cli/`
- elder_cli.py

### 4. ドキュメント
**From**: `docs/`
**To**: `elders_guild/docs/`
- philosophy/AI_DECISION_MAKER_PARADIGM.md
- NEW_ELDERS_GUILD_OVERVIEW.md
- guides/ELDER_COMMAND_GUIDE.md
- guides/AI_IMPLEMENTATION_GUIDELINES.md
- proposals/ELDER_COMMAND_UNIFICATION_PLAN.md
- proposals/AI_PARADIGM_REFACTORING_PLAN.md
- technical/NEW_ELDERS_GUILD_A2A_ARCHITECTURE.md

### 5. スクリプト
**From**: `scripts/`
**To**: `elders_guild/scripts/`
- setup-elder-commands.sh
- start-quality-servants.sh
- stop-quality-servants.sh
- deploy-quality-pipeline.sh

### 6. テスト
**From**: `tests/`
**To**: `elders_guild/tests/quality/`
- integration/test_quality_servants_mock.py
- integration/test_quality_servants_integration.py

## 依存関係修正

1. **インポートパス変更**
   - `from libs.quality.*` → `from elders_guild.quality.*`
   - `from libs.quality.servants.*` → `from elders_guild.quality_servants.*`

2. **スクリプトパス変更**
   - すべてのスクリプト内のパスを新しい場所に更新

3. **テストパス変更**
   - テスト内のインポートパスを更新

## 実行手順

1. ディレクトリ構造作成
2. ファイルコピー
3. インポートパス修正
4. スクリプトパス修正
5. テスト実行
6. 動作確認