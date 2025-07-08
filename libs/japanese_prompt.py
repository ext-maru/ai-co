
LANGUAGE_INSTRUCTION = '''
【重要】以下の指示に従って応答してください：
1. 全ての応答は日本語で行ってください
2. コード内のコメントも日本語で記述してください
3. ログメッセージ、エラーメッセージも日本語にしてください
4. ただし、変数名、関数名、クラス名は英語のままにしてください
5. ファイル名も英語のままにしてください

例:
- ✅ self.logger.info("タスク処理を開始します")
- ✅ # ユーザー情報を取得
- ❌ self.logger.info("Processing task")
- ❌ # Get user information
'''

# TaskWorkerのプロンプトに追加する関数
def add_japanese_instruction(prompt: str) -> str:
    """プロンプトに日本語指示を追加"""
    return LANGUAGE_INSTRUCTION + "\n\n" + prompt
