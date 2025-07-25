#!/usr/bin/env python3
"""
Simple Abstract Method Fixer
シンプルに抽象メソッドの実装を追加
"""

import os
import ast
from pathlib import Path
from datetime import datetime
import sqlite3

def get_violations():
    """違反をデータベースから取得"""
    db_path = Path("data/abstract_violations.db")
    if not db_path.exists():
        print("❌ 違反データベースが見つかりません")
        return []

    conn = sqlite3connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT file_path, class_name, missing_method
        FROM violations
        WHERE status = 'open'
        ORDER BY file_path, class_name
    """
    )

    results = cursor.fetchall()
    conn.close()
    return results

def generate_method_implementation(method_name):
    """メソッドの基本実装を生成"""
    implementations = {
        "validate_config": '''
    def validate_config(self, config):
        """設定検証"""
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")

        # 必須キーチェック
        required_keys = getattr(self, 'REQUIRED_CONFIG_KEYS', [])
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")

        return True''',
        "handle_error": '''
    async def handle_error(self, error, context=None):
        """エラーハンドリング"""
        error_msg = f"Error in {self.__class__.__name__}: {str(error)}"

        if hasattr(self, 'logger'):
            self.logger.error(error_msg)
            if context:
                self.logger.error(f"Context: {context}")

        # エラー履歴に追加
        if hasattr(self, 'error_history'):
            self.error_history.append({
                'error': str(error),
                'context': context,
                'timestamp': datetime.now().isoformat()
            })

        # インシデントマネージャーへの報告（存在する場合）
        if hasattr(self, 'incident_manager'):
            await self.incident_manager.report(error, context)''',
        "get_status": '''
    def get_status(self):
        """ステータス取得"""
        return {
            "running": getattr(self, 'running', False),
            "name": self.__class__.__name__,
            "processed_count": getattr(self, 'processed_count', 0),
            "error_count": len(getattr(self, 'error_history', [])),
            "last_activity": getattr(self, 'last_activity', None),
            "health": self._check_health() if hasattr(self, '_check_health') else "unknown"
        }''',
        "cleanup": '''
    async def cleanup(self):
        """クリーンアップ処理"""
        if hasattr(self, 'logger'):
            self.logger.info(f"{self.__class__.__name__} cleanup started")

        try:
            # 実行中タスクのキャンセル
            if hasattr(self, 'active_tasks'):
                for task in self.active_tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*self.active_tasks, return_exceptions=True)

            # リソース解放
            if hasattr(self, 'connection') and self.connection:
                await self.connection.close()

            # 一時ファイル削除

                import shutil

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Cleanup error: {e}")

        if hasattr(self, 'logger'):
            self.logger.info(f"{self.__class__.__name__} cleanup completed")''',
        "initialize": '''
    async def initialize(self):
        """初期化処理"""
        if hasattr(self, 'logger'):
            self.logger.info(f"{self.__class__.__name__} initialization started")

        try:
            # 基本属性初期化
            self.running = False
            self.processed_count = 0
            self.error_history = []
            self.start_time = datetime.now()
            self.last_activity = None
            self.active_tasks = set()

            # 設定検証
            if hasattr(self, 'config'):
                if hasattr(self, 'validate_config'):
                    if not self.validate_config(self.config):
                        raise ValueError("Config validation failed")

            # 必要なディレクトリ作成
            if hasattr(self, 'work_dir'):
                self.work_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Initialization error: {e}")
            raise

        if hasattr(self, 'logger'):
            self.logger.info(f"{self.__class__.__name__} initialization completed")''',
        "stop": '''
    async def stop(self):
        """停止処理"""
        if hasattr(self, 'logger'):
            self.logger.info(f"{self.__class__.__name__} stopping")

        self.running = False

        # クリーンアップ実行
        if hasattr(self, 'cleanup'):
            await self.cleanup()

        if hasattr(self, 'logger'):
            self.logger.info(f"{self.__class__.__name__} stopped")''',
        "process_message": '''
    async def process_message(self, message):
        """メッセージ処理"""
        if hasattr(self, 'logger'):

        try:
            # メッセージ処理のデフォルト実装
            result = await self._handle_message(message) if hasattr(self, '_handle_message') else None

            # 処理カウント更新
            if hasattr(self, 'processed_count'):
                self.processed_count += 1

            # 最終活動時刻更新
            if hasattr(self, 'last_activity'):
                self.last_activity = datetime.now()

            return result

        except Exception as e:
            if hasattr(self, 'handle_error'):
                await self.handle_error(e, {'message': message})
            raise''',
    }

    # デフォルト実装
    default_impl = f'''
    def {method_name}(self, *args, **kwargs):
        """{method_name} default implementation"""
        if hasattr(self, 'logger'):

        pass'''

    return implementations.get(method_name, default_impl)

def add_imports_if_needed(content):
    """必要なインポートを追加"""
    imports_needed = []

    if "datetime" in content and "from datetime import datetime" not in content:
        imports_needed.append("from datetime import datetime")

    if "asyncio" in content and "import asyncio" not in content:
        imports_needed.append("import asyncio")

    if not imports_needed:
        return content

    # インポート文を適切な位置に挿入
    lines = content.split("\n")
    import_index = 0

    # 既存のインポートの最後を探す
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            import_index = i + 1
        # 複雑な条件判定
        elif import_index > 0 and line and not line.startswith(" "):
            break

    # インポートを挿入
    for imp in imports_needed:
        lines.insert(import_index, imp)
        import_index += 1

    return "\n".join(lines)

def fix_file(file_path, violations):
    """ファイルの違反を修正"""
    if not Path(file_path).exists():
        print(f"⚠️  スキップ: {file_path} (存在しません)")
        return 0

    print(f"\n🔧 修正中: {file_path}")

    with open(file_path, "r") as f:
        content = f.read()

    original_content = content
    fixed_count = 0

    # クラスごとに違反をグループ化
    class_violations = {}
    for _, class_name, method in violations:
        if class_name not in class_violations:
            class_violations[class_name] = []
        class_violations[class_name].append(method)

    # 各クラスの修正
    for class_name, methods in class_violations.items():
        print(f"  📝 クラス: {class_name}")

        # クラスの終了位置を探す
        class_pattern = f"class {class_name}"
        class_index = content.find(class_pattern)

        if class_index == -1:
            print(f"    ❌ クラス定義が見つかりません")
            continue

        # 次のクラスの開始位置を探す
        next_class_pattern = "\nclass "
        next_class_index = content.find(next_class_pattern, class_index + 1)

        # クラスの範囲を特定
        if next_class_index == -1:
            class_content = content[class_index:]
        else:
            class_content = content[class_index:next_class_index]

        # 各メソッドを追加
        for method in methods:
            # メソッドが既に存在するかチェック
            if (
                f"def {method}" in class_content
                or f"async def {method}" in class_content
            ):
                print(f"    ⚠️  {method} は既に存在します")
                continue

            print(f"    ✅ {method} を追加")

            # メソッド実装を生成
            implementation = generate_method_implementation(method)

            # インデントを調整（クラス内なので4スペース）
            implementation = "\n".join(
                line if not line else "    " + line
                for line in implementation.split("\n")
            )

            # クラスの最後に追加
            if next_class_index == -1:
                content = content + "\n" + implementation
            else:
                insert_pos = class_index + len(class_content)
                content = (
                    content[:insert_pos] + "\n" + implementation + content[insert_pos:]
                )

            fixed_count += 1

    # 必要なインポートを追加
    content = add_imports_if_needed(content)

    # ファイルを保存
    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"  💾 保存完了")

    return fixed_count

def update_database(violations):
    """データベースを更新"""
    db_path = Path("data/abstract_violations.db")
    conn = sqlite3connect(db_path)
    cursor = conn.cursor()

    for file_path, class_name, method in violations:
        cursor.execute(
            """
            UPDATE violations
            SET status = 'resolved', fixed_at = ?
            WHERE file_path = ? AND class_name = ? AND missing_method = ?
        """,
            (datetime.now().isoformat(), file_path, class_name, method),
        )

    conn.commit()
    conn.close()

def main():
    """メイン処理"""
    print("🚀 Simple Abstract Method Fixer")
    print("=" * 60)

    # 違反を取得
    violations = get_violations()

    if not violations:
        print("✅ 修正が必要な違反はありません")
        return

    print(f"\n📊 違反数: {len(violations)}")

    # ファイルごとにグループ化
    file_violations = {}
    for file_path, class_name, method in violations:
        if file_path not in file_violations:
            file_violations[file_path] = []
        file_violations[file_path].append((file_path, class_name, method))

    print(f"📁 対象ファイル数: {len(file_violations)}")

    # 各ファイルを修正
    total_fixed = 0
    fixed_violations = []

    for file_path, file_vios in file_violations.items():
        fixed = fix_file(file_path, file_vios)
        total_fixed += fixed

        if fixed > 0:
            fixed_violations.extend(file_vios[:fixed])

    # データベース更新
    if fixed_violations:
        update_database(fixed_violations)

    print("\n" + "=" * 60)
    print(f"✅ 修正完了: {total_fixed}件")
    print(f"⚠️  未修正: {len(violations) - total_fixed}件")

if __name__ == "__main__":
    main()
