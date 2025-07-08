#!/usr/bin/env python3
"""
Knowledge Base MCP Server
ナレッジベースの検索、追加、更新を行うMCPサーバー
"""

import sys
from pathlib import Path
import json
import asyncio
import re

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.mcp_wrapper import MCPServer

class KnowledgeBaseMCPServer:
    """ナレッジベース管理MCPサーバー"""
    
    def __init__(self):
        self.server = MCPServer("knowledge")
        self.kb_dir = PROJECT_ROOT / "knowledge_base"
        self.setup_tools()
    
    def setup_tools(self):
        @self.server.tool()
        async def search_knowledge(query: str, category: str = None):
            """ナレッジベースを検索"""
            results = []
            
            # 検索対象のファイル
            kb_files = list(self.kb_dir.glob("*.md"))
            if category:
                kb_files = [f for f in kb_files if category.lower() in f.name.lower()]
            
            # 各ファイルを検索
            for kb_file in kb_files:
                try:
                    content = kb_file.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    
                    # 検索
                    for i, line in enumerate(lines):
                        if query.lower() in line.lower():
                            # コンテキストを含めて返す
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = '\n'.join(lines[start:end])
                            
                            results.append({
                                'file': kb_file.name,
                                'line': i + 1,
                                'context': context,
                                'match': line.strip()
                            })
                except Exception as e:
                    print(f"Error reading {kb_file}: {e}")
            
            return {
                'query': query,
                'results_count': len(results),
                'results': results[:10]  # 最初の10件
            }
        
        @self.server.tool()
        async def add_knowledge(category: str, title: str, content: str):
            """ナレッジベースに新しい知識を追加"""
            # ファイル名を決定
            file_name = f"{category.upper()}_KB.md"
            kb_file = self.kb_dir / file_name
            
            # 既存の内容を読む
            if kb_file.exists():
                existing_content = kb_file.read_text(encoding='utf-8')
            else:
                existing_content = f"# {category.title()} Knowledge Base\n\n"
            
            # 新しいセクションを追加
            new_section = f"\n\n## {title}\n\n{content}\n"
            
            # タイムスタンプを追加
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_section += f"\n*Added: {timestamp}*\n"
            
            # ファイルに書き込み
            updated_content = existing_content + new_section
            kb_file.write_text(updated_content, encoding='utf-8')
            
            return {
                'status': 'success',
                'file': file_name,
                'title': title,
                'message': f'Knowledge added to {file_name}'
            }
        
        @self.server.tool()
        async def get_best_practices(topic: str):
            """特定のトピックのベストプラクティスを取得"""
            # ベストプラクティスを検索
            practices = []
            
            # 関連ファイルを探す
            for kb_file in self.kb_dir.glob("*BEST_PRACTICES*.md"):
                try:
                    content = kb_file.read_text(encoding='utf-8')
                    
                    # トピックに関連するセクションを探す
                    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
                    for section in sections:
                        if topic.lower() in section.lower():
                            lines = section.split('\n')
                            title = lines[0] if lines else 'Unknown'
                            practices.append({
                                'file': kb_file.name,
                                'title': title,
                                'content': '\n'.join(lines[1:]).strip()[:500]  # 最初の500文字
                            })
                except Exception as e:
                    print(f"Error reading {kb_file}: {e}")
            
            return {
                'topic': topic,
                'practices_count': len(practices),
                'practices': practices[:5]  # 最初の5件
            }
        
        @self.server.tool()
        async def analyze_errors(error_message: str):
            """エラーメッセージから解決策を検索"""
            solutions = []
            
            # エラー解決ナレッジを検索
            error_kb_files = [
                f for f in self.kb_dir.glob("*.md")
                if 'error' in f.name.lower() or 'troubleshoot' in f.name.lower()
            ]
            
            # 通常のナレッジも検索
            all_kb_files = list(self.kb_dir.glob("*.md"))
            
            for kb_file in set(error_kb_files + all_kb_files):
                try:
                    content = kb_file.read_text(encoding='utf-8')
                    
                    # エラーに関連する部分を探す
                    if error_message.lower() in content.lower():
                        # 関連セクションを抽出
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if error_message.lower() in line.lower():
                                # 解決策を探す
                                start = max(0, i - 5)
                                end = min(len(lines), i + 10)
                                context = '\n'.join(lines[start:end])
                                
                                solutions.append({
                                    'file': kb_file.name,
                                    'context': context,
                                    'relevance': 'high' if 'solution' in context.lower() or 'fix' in context.lower() else 'medium'
                                })
                except Exception as e:
                    print(f"Error reading {kb_file}: {e}")
            
            # 関連度でソート
            solutions.sort(key=lambda x: x['relevance'], reverse=True)
            
            return {
                'error': error_message,
                'solutions_count': len(solutions),
                'solutions': solutions[:3]  # 最初の3件
            }
    
    async def process_request(self, request_json):
        request = json.loads(request_json)
        return await self.server.handle_request(request)

# CLI interface
if __name__ == "__main__":
    import asyncio
    
    server = KnowledgeBaseMCPServer()
    
    # Read request from stdin
    request = input()
    
    # Process and return result
    result = asyncio.run(server.process_request(request))
    print(json.dumps(result))
