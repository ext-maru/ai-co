#!/usr/bin/env python3
"""
Phase 1: AIコマンドのカテゴリー分類と整理
現行54個のコマンドを新体系に向けて分類
"""

import os
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Tuple

class AICommandCategorizer:
    """AIコマンド分類システム"""
    
    def __init__(self):
        self.scripts_dir = Path("/home/aicompany/ai_co/scripts")
        self.timestamp = datetime.now()
        
        # 新カテゴリー定義
        self.new_categories = {
            "core": {
                "name": "Core Commands",
                "description": "基本システムコマンド",
                "prefix": None,  # No prefix for core commands
                "commands": []
            },
            "elder": {
                "name": "Elder Management",
                "description": "エルダー管理機能",
                "prefix": "elder",
                "commands": []
            },
            "worker": {
                "name": "Worker Management",
                "description": "ワーカー管理",
                "prefix": "worker",
                "commands": []
            },
            "dev": {
                "name": "Development Tools",
                "description": "開発ツール",
                "prefix": "dev",
                "commands": []
            },
            "test": {
                "name": "Testing Tools",
                "description": "テストツール",
                "prefix": "test",
                "commands": []
            },
            "ops": {
                "name": "Operations",
                "description": "運用ツール",
                "prefix": "ops",
                "commands": []
            },
            "monitor": {
                "name": "Monitoring",
                "description": "監視・ログ",
                "prefix": "monitor",
                "commands": []
            },
            "integration": {
                "name": "Integrations",
                "description": "外部連携",
                "prefix": "integrate",
                "commands": []
            }
        }
        
    def scan_commands(self) -> List[str]:
        """現行AIコマンドのスキャン"""
        ai_commands = []
        for file in self.scripts_dir.glob("ai-*"):
            if file.is_file() and os.access(file, os.X_OK):
                ai_commands.append(file.name)
        return sorted(ai_commands)
    
    def categorize_command(self, command: str) -> Tuple[str, str]:
        """コマンドを新カテゴリーに分類"""
        # Remove 'ai-' prefix
        cmd_parts = command[3:].split('-')
        
        # Core commands
        if command in ['ai-start', 'ai-stop', 'ai-status', 'ai-help', 'ai-env']:
            return 'core', command[3:]
        
        # Elder commands
        elif cmd_parts[0] == 'elder' or command in ['ai-servant']:
            return 'elder', '-'.join(cmd_parts)
        
        # Worker commands
        elif cmd_parts[0] == 'worker' or command in ['ai-queue', 'ai-dlq']:
            return 'worker', '-'.join(cmd_parts)
        
        # Development commands
        elif cmd_parts[0] in ['codegen', 'tdd', 'git', 'document']:
            return 'dev', '-'.join(cmd_parts)
        
        # Test commands
        elif cmd_parts[0] == 'test' or 'test' in cmd_parts:
            return 'test', '-'.join(cmd_parts)
        
        # Operations commands
        elif cmd_parts[0] in ['api', 'dashboard', 'system']:
            return 'ops', '-'.join(cmd_parts)
        
        # Monitoring commands
        elif cmd_parts[0] in ['logs', 'status'] or 'monitor' in cmd_parts:
            return 'monitor', '-'.join(cmd_parts)
        
        # Integration commands
        elif cmd_parts[0] in ['slack', 'mcp', 'send']:
            return 'integration', '-'.join(cmd_parts)
        
        # Special cases
        elif cmd_parts[0] == 'elf':
            return 'elder', 'elf-' + '-'.join(cmd_parts[1:])
        elif cmd_parts[0] == 'knights':
            return 'elder', 'knights-' + '-'.join(cmd_parts[1:])
        elif cmd_parts[0] == 'rag':
            return 'elder', 'rag-' + '-'.join(cmd_parts[1:])
        
        # Default to ops
        else:
            return 'ops', '-'.join(cmd_parts)
    
    def find_duplicates(self, categorized_commands: Dict) -> Dict[str, List[str]]:
        """重複・類似コマンドの検出"""
        duplicates = {}
        
        # 機能的に重複する可能性のあるコマンドグループ
        duplicate_groups = [
            # Status commands
            ['ai-status', 'ai-api-status', 'ai-system-status'],
            # Worker related
            ['ai-worker-health', 'ai-worker-status', 'ai-api-health'],
            # Elder related
            ['ai-elder', 'ai-elder-council', 'ai-elder-compliance'],
            # Test related
            ['ai-test-coverage', 'ai-test-quality', 'ai-test-runner'],
            # Send/Integration
            ['ai-send', 'ai-send-review', 'ai-send-status'],
        ]
        
        for group in duplicate_groups:
            existing = [cmd for cmd in group if cmd in [c['old_name'] for cat in categorized_commands.values() for c in cat['commands']]]
            if len(existing) > 1:
                duplicates[existing[0]] = existing[1:]
        
        return duplicates
    
    def create_migration_map(self, categorized_commands: Dict) -> Dict[str, str]:
        """旧コマンドから新コマンドへのマッピング作成"""
        migration_map = {}
        
        for category, data in categorized_commands.items():
            prefix = data['prefix']
            
            for cmd_info in data['commands']:
                old_name = cmd_info['old_name']
                new_name = cmd_info['new_name']
                
                if category == 'core':
                    # Core commands don't change
                    migration_map[old_name] = f"ai {new_name}"
                else:
                    # Category commands
                    migration_map[old_name] = f"ai {prefix} {new_name}"
        
        return migration_map
    
    def generate_report(self):
        """分類レポートの生成"""
        print("🔍 AIコマンド分類開始...")
        
        # Scan current commands
        commands = self.scan_commands()
        print(f"✅ {len(commands)}個のコマンドを検出")
        
        # Categorize commands
        categorized = self.new_categories.copy()
        
        for cmd in commands:
            category, new_name = self.categorize_command(cmd)
            
            # Special handling for new names
            if category == 'core':
                display_name = new_name
            else:
                # Remove redundant prefixes
                parts = new_name.split('-')
                if parts[0] == categorized[category]['prefix']:
                    display_name = '-'.join(parts[1:]) if len(parts) > 1 else parts[0]
                else:
                    display_name = new_name
            
            categorized[category]['commands'].append({
                'old_name': cmd,
                'new_name': display_name,
                'description': f"Migrated from {cmd}"
            })
        
        # Find duplicates
        duplicates = self.find_duplicates(categorized)
        
        # Create migration map
        migration_map = self.create_migration_map(categorized)
        
        # Generate report
        report = {
            "timestamp": self.timestamp.isoformat(),
            "total_commands": len(commands),
            "categorization": categorized,
            "duplicates": duplicates,
            "migration_map": migration_map,
            "statistics": {
                category: len(data['commands']) 
                for category, data in categorized.items()
            }
        }
        
        # Save report
        reports_dir = Path("/home/aicompany/ai_co/reports")
        json_path = reports_dir / f"ai_command_categorization_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Create markdown report
        self.create_markdown_report(report, json_path)
        
        return report, json_path
    
    def create_markdown_report(self, report: Dict, json_path: Path):
        """Markdown形式のレポート作成"""
        md_content = f"""# AIコマンド分類レポート

**作成日時**: {self.timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}  
**総コマンド数**: {report['total_commands']}個

## 📊 新カテゴリー別分類結果

"""
        # Category summary
        for category, data in report['categorization'].items():
            if data['commands']:
                md_content += f"### {data['name']} ({len(data['commands'])}個)\n"
                md_content += f"{data['description']}\n\n"
                
                md_content += "| 旧コマンド | 新コマンド |\n"
                md_content += "|------------|------------|\n"
                
                for cmd in data['commands']:
                    if category == 'core':
                        new_cmd = f"`ai {cmd['new_name']}`"
                    else:
                        new_cmd = f"`ai {data['prefix']} {cmd['new_name']}`"
                    md_content += f"| `{cmd['old_name']}` | {new_cmd} |\n"
                
                md_content += "\n"
        
        # Duplicates section
        if report['duplicates']:
            md_content += "## 🔄 重複・統合候補\n\n"
            for main, dups in report['duplicates'].items():
                md_content += f"- **{main}** と統合候補:\n"
                for dup in dups:
                    md_content += f"  - {dup}\n"
                md_content += "\n"
        
        # Statistics
        md_content += "## 📈 統計\n\n"
        md_content += "| カテゴリー | コマンド数 |\n"
        md_content += "|------------|------------|\n"
        
        for category, count in report['statistics'].items():
            if count > 0:
                md_content += f"| {report['categorization'][category]['name']} | {count} |\n"
        
        md_content += f"\n**合計**: {sum(report['statistics'].values())}個\n"
        
        # Migration examples
        md_content += "\n## 🔄 移行例\n\n```bash\n"
        # Show first 10 examples
        for old, new in list(report['migration_map'].items())[:10]:
            md_content += f"{old} → {new}\n"
        md_content += "```\n\n"
        
        md_content += f"*完全なマッピングは {json_path} を参照*\n"
        
        # Save markdown
        md_path = json_path.parent / f"AI_COMMAND_CATEGORIZATION_{self.timestamp.strftime('%Y%m%d')}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"📄 Markdownレポート保存: {md_path}")

def main():
    """メイン実行"""
    print("📋 Phase 1: AIコマンドカテゴリー分類")
    print("=" * 60)
    
    categorizer = AICommandCategorizer()
    report, json_path = categorizer.generate_report()
    
    print(f"\n✅ 分類完了!")
    print(f"\n📊 結果サマリー:")
    for category, count in report['statistics'].items():
        if count > 0:
            print(f"  - {report['categorization'][category]['name']}: {count}個")
    
    print(f"\n📄 レポート保存場所:")
    print(f"  - {json_path}")
    
    if report['duplicates']:
        print(f"\n⚠️ {len(report['duplicates'])}個の統合候補グループを検出")

if __name__ == "__main__":
    main()