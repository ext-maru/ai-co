#!/usr/bin/env python3
"""
Report Enhancer - 報告書品質向上エンジン
エルダー評議会での報告書ブラッシュアップ機能
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class ReportEnhancer:
    """報告書品質向上エンジン"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.enhancement_history = []
        
        # 改善パターン定義
        self.ambiguous_patterns = {
            r"多分|おそらく|かもしれない|思われる": "確定的な表現に変更",
            r"など|等|その他": "具体的な列挙に変更",
            r"いくつか|複数|様々な": "具体的な数量・種類を明記",
            r"最近|近頃|しばらく": "具体的な日時・期間を明記",
            r"大きな|小さな|多くの|少ない": "具体的な数値・割合を明記"
        }
        
        # 構造化テンプレート
        self.structure_templates = {
            "incident": {
                "sections": [
                    "## 問題の概要",
                    "## 発生日時・頻度",
                    "## 影響範囲",
                    "## 根本原因",
                    "## 実施した対応",
                    "## 検証結果",
                    "## 今後の対応"
                ],
                "required_info": {
                    "発生日時": r"\d{4}[-/]\d{2}[-/]\d{2}",
                    "エラーメッセージ": r"error|exception|failed",
                    "影響システム": r"service|component|module"
                }
            },
            "task": {
                "sections": [
                    "## タスク概要",
                    "## 背景・目的",
                    "## 実施内容",
                    "## 完了条件",
                    "## スケジュール",
                    "## リソース・担当者"
                ],
                "required_info": {
                    "期限": r"まで|by|期限",
                    "担当者": r"担当|assign|責任者",
                    "優先度": r"priority|優先"
                }
            },
            "knowledge": {
                "sections": [
                    "## 学習内容",
                    "## 背景・経緯",
                    "## 詳細説明",
                    "## 実装例・使用例",
                    "## 注意点・制限事項",
                    "## 関連情報"
                ],
                "required_info": {
                    "キーワード": r"keyword|tag",
                    "適用範囲": r"scope|range|対象"
                }
            }
        }
    
    def enhance_report(self, original_report: Dict) -> Dict:
        """報告書のブラッシュアップ"""
        self.logger.info(f"Enhancing report: {original_report.get('title', 'Untitled')}")
        
        enhanced = original_report.copy()
        enhancement_log = []
        
        # 1. 構造化の改善
        enhanced, structure_improvements = self._improve_structure(enhanced)
        if structure_improvements:
            enhancement_log.extend(structure_improvements)
        
        # 2. 曖昧表現の具体化
        enhanced, clarity_improvements = self._clarify_ambiguities(enhanced)
        if clarity_improvements:
            enhancement_log.extend(clarity_improvements)
        
        # 3. エビデンスの補強
        enhanced, evidence_improvements = self._add_evidence(enhanced)
        if evidence_improvements:
            enhancement_log.extend(evidence_improvements)
        
        # 4. アクションアイテムの明確化
        enhanced, action_improvements = self._clarify_actions(enhanced)
        if action_improvements:
            enhancement_log.extend(action_improvements)
        
        # 5. メタデータの充実
        enhanced = self._enrich_metadata(enhanced)
        
        # 改善履歴の記録
        if enhancement_log:
            enhanced['enhancement_log'] = enhancement_log
            enhanced['enhanced_at'] = datetime.now().isoformat()
            enhanced['enhancement_score'] = self._calculate_enhancement_score(
                original_report, enhanced
            )
        
        return enhanced
    
    def _improve_structure(self, report: Dict) -> Tuple[Dict, List[str]]:
        """構造化の改善"""
        improvements = []
        content = report.get('content', '')
        category = report.get('category', 'general')
        
        # カテゴリに応じたテンプレート選択
        if category in self.structure_templates:
            template = self.structure_templates[category]
            
            # 必要なセクションの確認
            missing_sections = []
            for section in template['sections']:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                # セクションの追加
                new_content = content + "\n\n"
                for section in missing_sections:
                    new_content += f"{section}\n[要記入]\n\n"
                
                report['content'] = new_content
                improvements.append(f"構造改善: {len(missing_sections)}個のセクションを追加")
        
        # 箇条書きの整形
        lines = content.split('\n')
        formatted_lines = []
        in_list = False
        
        for line in lines:
            # 箇条書きの検出と整形
            if re.match(r'^[\-\*]\s*(.+)', line):
                if not in_list:
                    formatted_lines.append('')  # 箇条書き前に空行
                    in_list = True
                formatted_lines.append(line)
            else:
                if in_list and line.strip():
                    formatted_lines.append('')  # 箇条書き後に空行
                    in_list = False
                formatted_lines.append(line)
        
        new_content = '\n'.join(formatted_lines)
        if new_content != content:
            report['content'] = new_content
            improvements.append("箇条書きの整形を実施")
        
        return report, improvements
    
    def _clarify_ambiguities(self, report: Dict) -> Tuple[Dict, List[str]]:
        """曖昧表現の具体化"""
        improvements = []
        content = report.get('content', '')
        
        # 曖昧なパターンの検出と提案
        ambiguous_found = []
        for pattern, suggestion in self.ambiguous_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                ambiguous_found.append({
                    'pattern': pattern,
                    'matches': list(set(matches)),
                    'suggestion': suggestion
                })
        
        if ambiguous_found:
            # 改善提案の生成
            clarification_notes = "\n\n## 📝 具体化が必要な箇所\n"
            for item in ambiguous_found:
                clarification_notes += f"- **{', '.join(item['matches'])}** → {item['suggestion']}\n"
            
            report['content'] += clarification_notes
            improvements.append(f"曖昧表現を{len(ambiguous_found)}箇所検出、具体化提案を追加")
        
        # 数値化可能な表現の検出
        quantifiable_patterns = [
            (r"(多|少な|大き|小さ)(い|く)", "具体的な数値で表現"),
            (r"(高|低)(い|く)", "具体的な数値・割合で表現"),
            (r"(速|遅)(い|く)", "具体的な時間・速度で表現")
        ]
        
        quantifiable_found = False
        for pattern, suggestion in quantifiable_patterns:
            if re.search(pattern, content):
                quantifiable_found = True
                break
        
        if quantifiable_found:
            report['content'] += "\n\n💡 **改善提案**: 定量的な表現を使用してください"
            improvements.append("定量化提案を追加")
        
        return report, improvements
    
    def _add_evidence(self, report: Dict) -> Tuple[Dict, List[str]]:
        """エビデンスの補強"""
        improvements = []
        content = report.get('content', '')
        
        # エビデンスの存在確認
        evidence_patterns = {
            'ログ': r'log|ログ|ERROR|WARN|INFO',
            'メトリクス': r'\d+%|\d+ms|\d+MB|\d+件',
            'スクリーンショット': r'screenshot|画像|image',
            'コード': r'```|コード|code',
            '参照': r'参照|reference|ref:|→'
        }
        
        missing_evidence = []
        for evidence_type, pattern in evidence_patterns.items():
            if not re.search(pattern, content, re.IGNORECASE):
                missing_evidence.append(evidence_type)
        
        if missing_evidence and report.get('category') in ['incident', 'task']:
            evidence_section = "\n\n## 📊 推奨エビデンス\n"
            evidence_section += "以下のエビデンスを追加することを推奨します：\n"
            for evidence in missing_evidence:
                evidence_section += f"- [ ] {evidence}\n"
            
            report['content'] += evidence_section
            improvements.append(f"エビデンス補強提案を{len(missing_evidence)}項目追加")
        
        # ファイルパス・行番号の検出と強調
        file_pattern = r'([/\w\-\.]+\.(py|js|yaml|json|md)):?(\d+)?'
        matches = re.findall(file_pattern, content)
        
        if matches:
            # ファイル参照を見つけやすく整形
            reference_section = "\n\n## 📁 関連ファイル\n"
            for match in matches:
                file_path = match[0] + '.' + match[1]
                line_num = match[2] if match[2] else ''
                if line_num:
                    reference_section += f"- `{file_path}:{line_num}`\n"
                else:
                    reference_section += f"- `{file_path}`\n"
            
            if "関連ファイル" not in content:
                report['content'] += reference_section
                improvements.append("ファイル参照を整理")
        
        return report, improvements
    
    def _clarify_actions(self, report: Dict) -> Tuple[Dict, List[str]]:
        """アクションアイテムの明確化"""
        improvements = []
        content = report.get('content', '')
        
        # アクション関連のキーワード検出
        action_keywords = [
            r'(実装|implement)',
            r'(修正|fix)',
            r'(調査|investigate)',
            r'(確認|check|verify)',
            r'(作成|create)',
            r'(更新|update)',
            r'(必要|need|require)'
        ]
        
        found_actions = []
        for keyword in action_keywords:
            matches = re.findall(f'.*{keyword}.*', content, re.IGNORECASE | re.MULTILINE)
            if matches:
                found_actions.extend(matches[:3])  # 最初の3つまで
        
        if found_actions and report.get('category') in ['task', 'incident']:
            # アクションアイテムの整理
            action_section = "\n\n## ✅ アクションアイテム\n"
            
            # 期限が明記されているか確認
            has_deadline = bool(re.search(r'期限|deadline|まで|by|\d{4}[-/]\d{2}[-/]\d{2}', content))
            if not has_deadline:
                action_section += "⚠️ **期限が設定されていません**\n\n"
            
            # 担当者が明記されているか確認
            has_assignee = bool(re.search(r'担当|assign|責任者|owner', content))
            if not has_assignee:
                action_section += "⚠️ **担当者が設定されていません**\n\n"
            
            # アクションの箇条書き
            action_section += "識別されたアクション：\n"
            for i, action in enumerate(found_actions, 1):
                action_clean = re.sub(r'^\s*[-*]\s*', '', action.strip())
                action_section += f"{i}. [ ] {action_clean}\n"
            
            if not has_deadline or not has_assignee:
                report['content'] += action_section
                improvements.append("アクションアイテムの明確化を実施")
        
        return report, improvements
    
    def _enrich_metadata(self, report: Dict) -> Dict:
        """メタデータの充実"""
        # タイムスタンプの追加
        if 'created_at' not in report:
            report['created_at'] = datetime.now().isoformat()
        
        if 'updated_at' not in report or report.get('updated_at') != report.get('created_at'):
            report['updated_at'] = datetime.now().isoformat()
        
        # 自動タグ生成
        if 'tags' not in report:
            report['tags'] = self._generate_tags(report)
        
        # 文字数・セクション数の記録
        content = report.get('content', '')
        report['metadata'] = {
            'char_count': len(content),
            'line_count': len(content.split('\n')),
            'section_count': len(re.findall(r'^#+\s', content, re.MULTILINE)),
            'has_code_blocks': bool(re.search(r'```', content)),
            'has_lists': bool(re.search(r'^\s*[-*]\s', content, re.MULTILINE))
        }
        
        return report
    
    def _generate_tags(self, report: Dict) -> List[str]:
        """自動タグ生成"""
        tags = []
        content = report.get('content', '').lower()
        category = report.get('category', '')
        
        # カテゴリタグ
        if category:
            tags.append(category)
        
        # 技術キーワードの抽出
        tech_keywords = {
            'error': ['error', 'exception', 'failed'],
            'performance': ['performance', 'slow', '遅い', 'optimization'],
            'security': ['security', 'vulnerability', 'auth'],
            'database': ['database', 'db', 'sql', 'query'],
            'api': ['api', 'endpoint', 'rest', 'graphql'],
            'monitoring': ['monitor', 'alert', 'metrics', 'ログ']
        }
        
        for tag, keywords in tech_keywords.items():
            for keyword in keywords:
                if keyword in content:
                    tags.append(tag)
                    break
        
        # 重複除去
        return list(set(tags))
    
    def _calculate_enhancement_score(self, original: Dict, enhanced: Dict) -> float:
        """改善スコアの計算"""
        score = 0.0
        
        # コンテンツの充実度
        original_content = original.get('content', '')
        enhanced_content = enhanced.get('content', '')
        
        # 文字数の増加
        char_increase = len(enhanced_content) - len(original_content)
        if char_increase > 0:
            score += min(0.3, char_increase / 1000)  # 1000文字増加で0.3点
        
        # セクション数の増加
        original_sections = len(re.findall(r'^#+\s', original_content, re.MULTILINE))
        enhanced_sections = len(re.findall(r'^#+\s', enhanced_content, re.MULTILINE))
        section_increase = enhanced_sections - original_sections
        if section_increase > 0:
            score += min(0.2, section_increase * 0.05)  # 1セクション増加で0.05点
        
        # メタデータの充実
        if 'tags' in enhanced and 'tags' not in original:
            score += 0.1
        if 'metadata' in enhanced:
            score += 0.1
        
        # エビデンスの追加
        if '推奨エビデンス' in enhanced_content or '関連ファイル' in enhanced_content:
            score += 0.2
        
        # アクションの明確化
        if 'アクションアイテム' in enhanced_content:
            score += 0.1
        
        return min(1.0, score)  # 最大1.0
    
    def analyze_enhancement_potential(self, report: Dict) -> Dict:
        """改善可能性の分析"""
        analysis = {
            'current_quality': self._assess_current_quality(report),
            'improvement_areas': [],
            'estimated_improvement_score': 0.0
        }
        
        content = report.get('content', '')
        
        # 構造の評価
        sections = len(re.findall(r'^#+\s', content, re.MULTILINE))
        if sections < 3:
            analysis['improvement_areas'].append('構造化不足')
            analysis['estimated_improvement_score'] += 0.2
        
        # 曖昧表現の評価
        ambiguous_count = 0
        for pattern in self.ambiguous_patterns.keys():
            if re.search(pattern, content):
                ambiguous_count += 1
        
        if ambiguous_count > 0:
            analysis['improvement_areas'].append(f'曖昧表現{ambiguous_count}箇所')
            analysis['estimated_improvement_score'] += min(0.3, ambiguous_count * 0.05)
        
        # エビデンスの評価
        has_evidence = bool(re.search(r'log|ログ|\d+%|```', content, re.IGNORECASE))
        if not has_evidence:
            analysis['improvement_areas'].append('エビデンス不足')
            analysis['estimated_improvement_score'] += 0.2
        
        # アクションの評価
        has_clear_actions = bool(re.search(r'期限|担当|□|\[ \]', content))
        if not has_clear_actions and report.get('category') in ['task', 'incident']:
            analysis['improvement_areas'].append('アクション不明確')
            analysis['estimated_improvement_score'] += 0.2
        
        analysis['estimated_improvement_score'] = min(1.0, analysis['estimated_improvement_score'])
        
        return analysis
    
    def _assess_current_quality(self, report: Dict) -> str:
        """現在の品質評価"""
        content = report.get('content', '')
        score = 0
        
        # 基本要素の確認
        if len(content) > 100:
            score += 1
        if re.search(r'^#+\s', content, re.MULTILINE):
            score += 1
        if re.search(r'^\s*[-*]\s', content, re.MULTILINE):
            score += 1
        if re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', content):
            score += 1
        if not any(re.search(pattern, content) for pattern in self.ambiguous_patterns.keys()):
            score += 1
        
        if score >= 4:
            return "高"
        elif score >= 2:
            return "中"
        else:
            return "低"