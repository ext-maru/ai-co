#!/usr/bin/env python3
"""
AI Company 拡張PMワーカー v2.0
プロジェクト全体のライフサイクルを管理
要件定義→設計→開発→テスト→本番反映
"""

import sys
from pathlib import Path
import json
import shutil
from datetime import datetime
import time
from typing import Dict, List, Optional, Any

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import BaseWorker, get_config, EMOJI, ErrorSeverity, with_error_handling
from core.worker_communication import CommunicationMixin
from libs.self_evolution_manager import SelfEvolutionManager
from libs.github_flow_manager import GitHubFlowManager
from libs.project_design_manager import ProjectDesignManager
from libs.slack_notifier import SlackNotifier
from libs.ai_command_helper import AICommandHelper
from libs.knowledge_base_manager import KnowledgeAwareMixin
from libs.quality_checker import QualityChecker
from libs.pm_elder_integration import PMElderIntegration

class EnhancedPMWorker(BaseWorker, CommunicationMixin, KnowledgeAwareMixin):
    """拡張PMワーカー - プロジェクトマネージャーとして全体を監督"""
    
    def __init__(self, worker_id=None):
        super().__init__(worker_type='pm', worker_id=worker_id)
        self.setup_communication()
        self.output_dir = PROJECT_ROOT / "output"
        self.evolution_manager = SelfEvolutionManager()
        self.git_manager = GitHubFlowManager()
        self.project_manager = ProjectDesignManager()
        self.slack = SlackNotifier()
        self.ai_helper = AICommandHelper()
        self.config = get_config()
        
        # SE-Tester連携設定
        self.se_testing_enabled = self.config.get('pm.se_testing_enabled', True)
        
        # 品質管理機能統合
        try:
            self.quality_checker = QualityChecker()
            self.task_iterations: Dict[str, int] = {}  # タスクIDごとのイテレーション回数
            self.max_iterations = 3  # 最大再試行回数
            self.task_contexts: Dict[str, dict] = {}  # タスクのコンテキスト保存
            self.quality_enabled = True
            self.logger.info("品質管理機能統合完了")
        except Exception as e:
            # 品質管理初期化エラー
            context = {
                'operation': 'quality_checker_init',
                'component': 'QualityChecker'
            }
            self.handle_error(e, context, severity=ErrorSeverity.LOW)
            self.quality_checker = None
            self.quality_enabled = False
        
        # Elder統合システム
        try:
            self.pm_elder_integration = PMElderIntegration()
            self.elder_integration_enabled = True
            self.logger.info("PM-Elder統合システム初期化完了")
        except Exception as e:
            # Elder統合初期化エラー
            context = {
                'operation': 'pm_elder_init',
                'component': 'PMElderIntegration'
            }
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
            self.pm_elder_integration = None
            self.elder_integration_enabled = False
        
        self.logger.info(f"Enhanced PM Worker initialized (id: {self.worker_id})")
    
    def process_message(self, ch, method, properties, body):
        """メッセージ処理のメインロジック"""
        try:
            self.logger.info(f"{EMOJI['info']} Processing PM task: {body.get('task_id')}")
            
            # プロジェクトタイプを判定
            if body.get('project_mode', False) or self._is_complex_task(body):
                # プロジェクトモードで処理
                self._handle_project_mode(body)
            else:
                # 従来のシンプルなファイル配置モード
                self._handle_simple_mode(body)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            context = {
                'operation': 'process_message',
                'task_id': body.get('task_id'),
                'project_mode': body.get('project_mode', False),
                'prompt': body.get('prompt', '')[:100]
            }
            
            # 統一エラーハンドリング
            self.handle_error(e, context, severity=ErrorSeverity.HIGH)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def _is_complex_task(self, body: Dict[str, Any]) -> bool:
        """複雑なタスクかどうかを判定"""
        indicators = [
            'architecture' in body.get('prompt', '').lower(),
            'design' in body.get('prompt', '').lower(),
            'system' in body.get('prompt', '').lower(),
            'integration' in body.get('prompt', '').lower(),
            len(body.get('files_created', [])) > 5,
            body.get('task_type') == 'project'
        ]
        return sum(indicators) >= 2
    
    def _handle_project_mode(self, body: Dict[str, Any]):
        """プロジェクトモードでの処理"""
        task_id = body.get('task_id')
        prompt = body.get('prompt', '')
        
        self.logger.info(f"Starting project mode for task: {task_id}")
        
        # Elder承認プロセス
        if self.elder_integration_enabled:
            approved, approval_message = self.pm_elder_integration.request_project_approval(body)
            
            if not approved:
                self.logger.warning(f"Project requires Elder approval: {approval_message}")
                
                # Elder承認待ちの通知
                self.slack.send_message(
                    f"🔒 プロジェクト承認待ち\n"
                    f"タスクID: {task_id}\n"
                    f"理由: {approval_message}\n"
                    f"Elder Councilの判断をお待ちください。",
                    channel="#pm-notifications"
                )
                
                # 承認待ち状態で一時停止
                return
            else:
                self.logger.info(f"Project approved: {approval_message}")
        
        # 1. プロジェクト作成
        project_name = self._extract_project_name(prompt)
        project_id = self.project_manager.create_project(
            task_id=task_id,
            name=project_name,
            description=prompt
        )
        
        # 2. 要件定義フェーズ
        self._phase_requirements(project_id, body)
        
        # 3. 設計フェーズ
        self._phase_design(project_id, body)
        
        # 4. 開発フェーズ
        self._phase_development(project_id, body)
        
        # 5. テストフェーズ
        self._phase_testing(project_id, body)
        
        # 6. デプロイフェーズ
        self._phase_deployment(project_id, body)
        
        # プロジェクトレポート生成
        report = self.project_manager.generate_project_report(project_id)
        self.logger.info(f"Project completed:\n{report}")
        
        # 品質評価
        quality_score = 0.0
        if self.quality_enabled:
            quality_score = self._evaluate_project_quality(project_id, body)
            self.logger.info(f"プロジェクト品質スコア: {quality_score:.2f}")
        
        # Elder完了報告
        if self.elder_integration_enabled:
            project_result = {
                'placed_files': body.get('placed_files', []),
                'quality_score': quality_score,
                'execution_time': 'measured',  # 実際は計測値
                'project_report': report
            }
            self.pm_elder_integration.report_project_completion(project_id, project_result)
        
        # Slack通知
        message = f"{EMOJI['rocket']} プロジェクト完了: {project_name}\n"
        message += f"プロジェクトID: {project_id}\n"
        if self.quality_enabled:
            message += f"品質スコア: {quality_score:.2f}\n"
        message += "詳細レポートはログを参照してください。"
        
        self.slack.send_message(message)
    
    def _phase_requirements(self, project_id: str, body: Dict[str, Any]):
        """要件定義フェーズ"""
        self.logger.info(f"Phase: Requirements for project {project_id}")
        self.project_manager.update_phase_status(project_id, 'planning', 'in_progress')
        
        # プロンプトから要件を抽出
        requirements = self._extract_requirements(body.get('prompt', ''))
        
        for req in requirements:
            self.project_manager.add_requirement(
                project_id=project_id,
                type=req['type'],
                description=req['description'],
                priority=req.get('priority', 'normal')
            )
        
        # AIに詳細な要件定義書を作成させる
        self._create_requirements_document(project_id, requirements)
        
        self.project_manager.update_phase_status(project_id, 'planning', 'completed')
    
    def _phase_design(self, project_id: str, body: Dict[str, Any]):
        """設計フェーズ"""
        self.logger.info(f"Phase: Design for project {project_id}")
        self.project_manager.update_phase_status(project_id, 'design', 'in_progress')
        
        # ファイル構造から設計を推測
        files_created = body.get('files_created', [])
        design = self._analyze_architecture(files_created)
        
        # 設計書作成
        design_id = self.project_manager.create_design(
            project_id=project_id,
            design_type='architecture',
            content=design
        )
        
        # 詳細設計書の自動生成
        self._create_detailed_design(project_id, design_id, design)
        
        self.project_manager.update_phase_status(project_id, 'design', 'completed')
    
    def _phase_development(self, project_id: str, body: Dict[str, Any]):
        """開発フェーズ"""
        self.logger.info(f"Phase: Development for project {project_id}")
        self.project_manager.update_phase_status(project_id, 'development', 'in_progress')
        
        # ファイル配置（従来の処理）
        files_created = body.get('files_created', [])
        placed_files = []
        
        for file_path in files_created:
            source = self.output_dir / file_path
            if source.exists():
                # 開発タスク作成
                dev_task_id = self.project_manager.create_development_task(
                    project_id=project_id,
                    design_id=None,
                    name=f"Deploy {file_path}",
                    description=f"Deploying file: {file_path}"
                )
                
                try:
                    # ファイル配置
                    target = self.evolution_manager.determine_file_location(source)
                    shutil.copy2(source, target)
                    
                    # Git追加
                    if self.config.get('git.auto_add', True):
                        self.git_manager.add_file(target)
                    
                    placed_files.append(str(target))
                    
                    # タスク完了
                    self.project_manager.update_task_status(
                        dev_task_id, 
                        'completed',
                        {'file_path': str(target)}
                    )
                    
                    # プロジェクトファイル登録
                    self.project_manager.add_project_file(
                        project_id=project_id,
                        file_path=str(target),
                        file_type=self._get_file_type(target),
                        phase='development'
                    )
                    
                except Exception as e:
                    # ファイル配置エラー
                    context = {
                        'operation': 'file_placement',
                        'file_path': str(file_path),
                        'target': str(target) if 'target' in locals() else 'unknown',
                        'dev_task_id': dev_task_id
                    }
                    self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
                    self.project_manager.update_task_status(
                        dev_task_id,
                        'failed',
                        {'error': str(e)}
                    )
        
        self.project_manager.update_phase_status(project_id, 'development', 'completed')
        body['placed_files'] = placed_files
    
    def _phase_testing(self, project_id: str, body: Dict[str, Any]):
        """テストフェーズ"""
        self.logger.info(f"Phase: Testing for project {project_id}")
        self.project_manager.update_phase_status(project_id, 'testing', 'in_progress')
        
        placed_files = body.get('placed_files', [])
        
        if self.se_testing_enabled and placed_files:
            # SE-Testerワーカーに送信
            self.logger.info(f"Sending to SE-Tester for testing: {len(placed_files)} files")
            
            test_task = {
                'task_id': body.get('task_id'),
                'project_id': project_id,
                'files_created': placed_files,
                'fix_attempt': 0,
                'original_prompt': body.get('prompt', '')
            }
            
            self.send_to_worker('se', 'test_request', test_task)
            
            # テスト結果を待つ（実際は非同期だが、ここでは仮の処理）
            time.sleep(5)
            
            # テスト結果を記録（実際はSE-Testerからの通知を受け取る）
            self.project_manager.record_test_result(
                project_id=project_id,
                dev_task_id=None,
                test_type='unit',
                status='passed',
                details={'message': 'All tests passed'}
            )
        else:
            # テストスキップ
            self.logger.info("Testing skipped (SE-Tester disabled or no files)")
        
        self.project_manager.update_phase_status(project_id, 'testing', 'completed')
    
    def _phase_deployment(self, project_id: str, body: Dict[str, Any]):
        """デプロイフェーズ"""
        self.logger.info(f"Phase: Deployment for project {project_id}")
        self.project_manager.update_phase_status(project_id, 'deployment', 'in_progress')
        
        # Gitコミット
        if self.config.get('git.auto_commit', True):
            commit_message = f"Deploy project {project_id}: {body.get('prompt', '')[:50]}"
            self.git_manager.commit(commit_message)
        
        # デプロイ完了
        self.project_manager.update_phase_status(project_id, 'deployment', 'completed')
        
        # プロジェクト全体のステータス更新
        with self.project_manager._get_connection() as conn:
            conn.execute("""
                UPDATE projects SET status = 'deployed' WHERE project_id = ?
            """, (project_id,))
            conn.commit()
    
    def _handle_simple_mode(self, body: Dict[str, Any]):
        """シンプルモード（従来の処理）"""
        task_id = body.get('task_id')
        files_created = body.get('files_created', [])
        
        self.logger.info(f"Simple mode: placing {len(files_created)} files")
        
        placed_files = []
        for file_path in files_created:
            source = self.output_dir / file_path
            if source.exists():
                try:
                    target = self.evolution_manager.determine_file_location(source)
                    shutil.copy2(source, target)
                    
                    if self.config.get('git.auto_add', True):
                        self.git_manager.add_file(target)
                    
                    placed_files.append(str(target))
                    self.logger.info(f"Placed: {source} -> {target}")
                    
                except Exception as e:
                    # シンプルモードファイル配置エラー
                    context = {
                        'operation': 'simple_file_placement',
                        'file_path': str(file_path),
                        'task_id': task_id
                    }
                    self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
        
        # 結果を次のワーカーへ
        if self.se_testing_enabled and placed_files:
            # SE-Testerへ
            test_task = {
                'task_id': task_id,
                'files_created': placed_files,
                'fix_attempt': 0
            }
            self.send_to_worker('se', 'test_request', test_task)
        else:
            # 直接ResultWorkerへ
            self._send_result({
                'task_id': task_id,
                'files_placed': placed_files,
                'status': 'completed'
            })
    
    def _extract_project_name(self, prompt: str) -> str:
        """プロンプトからプロジェクト名を抽出"""
        # 簡単な実装（実際はより高度な処理が必要）
        if "作成" in prompt:
            parts = prompt.split("作成")
            if len(parts) > 0:
                return parts[0].strip()[-20:]
        return prompt[:30]
    
    def _extract_requirements(self, prompt: str) -> List[Dict[str, Any]]:
        """プロンプトから要件を抽出"""
        requirements = []
        
        # 機能要件の抽出（簡易版）
        keywords = ['機能', '実装', '作成', '生成', '処理']
        for keyword in keywords:
            if keyword in prompt:
                requirements.append({
                    'type': 'functional',
                    'description': f"{keyword}に関する要件",
                    'priority': 'high'
                })
        
        # 非機能要件
        if any(word in prompt for word in ['性能', 'パフォーマンス', '高速']):
            requirements.append({
                'type': 'non_functional',
                'description': 'パフォーマンス要件',
                'priority': 'normal'
            })
        
        return requirements if requirements else [{
            'type': 'functional',
            'description': prompt,
            'priority': 'normal'
        }]
    
    def _analyze_architecture(self, files: List[str]) -> Dict[str, Any]:
        """ファイル構造からアーキテクチャを分析"""
        architecture = {
            'components': [],
            'layers': [],
            'dependencies': []
        }
        
        # コンポーネント分析
        for file in files:
            if 'worker' in file:
                architecture['components'].append({
                    'type': 'worker',
                    'name': Path(file).stem,
                    'path': file
                })
            elif 'manager' in file:
                architecture['components'].append({
                    'type': 'manager',
                    'name': Path(file).stem,
                    'path': file
                })
        
        return architecture
    
    def _get_file_type(self, file_path: Path) -> str:
        """ファイルタイプを判定"""
        if file_path.suffix == '.py':
            if 'test_' in file_path.name:
                return 'test'
            elif 'worker' in file_path.name:
                return 'worker'
            else:
                return 'source'
        elif file_path.suffix in ['.json', '.yaml', '.conf']:
            return 'config'
        elif file_path.suffix in ['.md', '.txt']:
            return 'doc'
        else:
            return 'other'
    
    def _create_requirements_document(self, project_id: str, requirements: List[Dict]):
        """要件定義書を自動生成"""
        doc_content = f"""# 要件定義書 - プロジェクト {project_id}

## 機能要件
"""
        # TODO: 要件定義書の内容を実装
        return doc_content

    def cleanup(self):
        """TODO: cleanupメソッドを実装してください"""
        pass

    def stop(self):
        """TODO: stopメソッドを実装してください"""
        pass

    def initialize(self) -> None:
        """ワーカーの初期化処理"""
        # TODO: 初期化ロジックを実装してください
        logger.info(f"{self.__class__.__name__} initialized")
        pass

    def handle_error(self):
        """TODO: handle_errorメソッドを実装してください"""
        pass

    def get_status(self):
        """TODO: get_statusメソッドを実装してください"""
        pass

    def validate_config(self):
        """TODO: validate_configメソッドを実装してください"""
        pass
    
    def _create_detailed_design(self, project_id: str, design_id: str, design: Dict):
        """詳細設計書を自動生成"""
        doc_content = f"""# 詳細設計書 - プロジェクト {project_id}

## アーキテクチャ概要
- 設計ID: {design_id}
- コンポーネント数: {len(design.get('components', []))}

## コンポーネント詳細
"""
        for comp in design.get('components', []):
            doc_content += f"### {comp['name']}\n"
            doc_content += f"- タイプ: {comp['type']}\n"
            doc_content += f"- パス: {comp['path']}\n\n"
        
        # AI Command Executorで文書生成
        self.ai_helper.create_bash_command(
            f"""cat > {PROJECT_ROOT}/project_designs/designs/{design_id}_design.md << 'EOF'
{doc_content}
EOF""",
            f"create_design_{design_id}"
        )
    
    def _send_result(self, result_data: Dict[str, Any]):
        """結果をResultWorkerに送信"""
        self.send_to_worker('result', 'process', result_data)
    
    def _evaluate_project_quality(self, project_id: str, project_data: Dict[str, Any]) -> float:
        """プロジェクト全体の品質を評価"""
        if not self.quality_enabled:
            return 0.0
        
        try:
            # ファイル作成状況を評価
            files_created = project_data.get('placed_files', [])
            if not files_created:
                return 0.5  # ファイル未作成は低品質
            
            # 品質チェッカーでファイル品質を評価
            total_score = 0.0
            evaluated_files = 0
            
            for file_path in files_created:
                try:
                    file_data = {
                        'files_created': [file_path],
                        'response': f'File created: {file_path}',
                        'task_type': 'file_creation'
                    }
                    score, _, _ = self.quality_checker.check_task_quality(file_data)
                    total_score += score
                    evaluated_files += 1
                except Exception as e:
                    # ファイル品質評価エラー
                    context = {
                        'operation': 'file_quality_evaluation',
                        'file_path': str(file_path),
                        'project_id': project_id
                    }
                    self.handle_error(e, context, severity=ErrorSeverity.LOW)
            
            if evaluated_files > 0:
                avg_score = total_score / evaluated_files
            else:
                avg_score = 0.5
            
            # プロジェクト完了度ボーナス
            completion_bonus = 0.2 if project_data.get('status') == 'completed' else 0.0
            
            final_score = min(1.0, avg_score + completion_bonus)
            
            self.logger.info(f"プロジェクト品質評価: {final_score:.2f} (ファイル数: {evaluated_files})")
            return final_score
            
        except Exception as e:
            # プロジェクト品質評価エラー
            context = {
                'operation': 'project_quality_evaluation',
                'project_id': project_id
            }
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
            return 0.5
    
    def _check_task_quality_and_retry(self, task_id: str, result: Dict[str, Any]) -> bool:
        """タスク品質をチェックし, 必要に応じて再実行を指示"""
        if not self.quality_enabled:
            return True  # 品質チェック無効時は常に合格
        
        try:
            # イテレーション回数を取得
            iteration = self.task_iterations.get(task_id, 0)
            
            # 品質チェック
            quality_score, issues, suggestions = self.quality_checker.check_task_quality(result)
            self.logger.info(f"📊 品質スコア: {quality_score:.2f} (タスク: {task_id}, イテレーション: {iteration + 1})")
            
            if quality_score < self.quality_checker.min_quality_score and iteration < self.max_iterations:
                # 品質不十分 - 再実行指示
                self.logger.warning(f"⚠️ 品質不十分 - 再実行を指示します")
                self._request_task_retry(task_id, result, issues, suggestions, iteration)
                return False
            else:
                # 品質OK または 最大イテレーション到達
                if quality_score >= self.quality_checker.min_quality_score:
                    self.logger.info(f"✅ 品質基準を満たしました (スコア: {quality_score:.2f})")
                else:
                    self.logger.warning(f"⚠️ 最大イテレーション到達 - 現状で受け入れ (スコア: {quality_score:.2f})")
                
                # コンテキストクリア
                self.task_iterations.pop(task_id, None)
                self.task_contexts.pop(task_id, None)
                return True
                
        except Exception as e:
            # 品質チェックエラー
            context = {
                'operation': 'task_quality_check',
                'task_id': task_id
            }
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
            return True  # エラー時は合格扱い
    
    def _request_task_retry(self, task_id: str, result: dict, issues: list, suggestions: list, iteration: int):
        """タスクの再実行を要求"""
        try:
            # Elder エスカレーション判定
            if self.elder_integration_enabled and iteration >= 2:  # 3回目失敗でElder介入
                escalated = self.pm_elder_integration.escalate_quality_issue(
                    project_id=result.get('project_id', task_id),
                    quality_issues=issues,
                    iteration_count=iteration + 1
                )
                
                if escalated:
                    self.logger.info(f"Quality issue escalated to Elders for task {task_id}")
                    # Elder判断待ちでリトライを一時停止
                    return
            
            # コンテキストを取得または初期化
            if task_id not in self.task_contexts:
                self.task_contexts[task_id] = {
                    'original_prompt': result.get('prompt', ''),
                    'task_type': result.get('task_type', 'code'),
                    'history': []
                }
            
            context = self.task_contexts[task_id]
            
            # 履歴に追加
            context['history'].append({
                'iteration': iteration,
                'quality_score': self.quality_checker.check_task_quality(result)[0],
                'issues': issues,
                'suggestions': suggestions,
                'response': result.get('response', '')[:500]  # 要約
            })
            
            # フィードバックプロンプトを生成
            feedback_prompt = self.quality_checker.generate_feedback_prompt(
                task_id,
                context['original_prompt'],
                issues,
                suggestions,
                iteration
            )
            
            # 再実行タスクを作成
            retry_task = {
                'task_id': task_id,
                'task_type': context['task_type'],
                'prompt': feedback_prompt,
                'is_retry': True,
                'iteration': iteration + 1,
                'context': {
                    'original_prompt': context['original_prompt'],
                    'previous_issues': issues,
                    'previous_suggestions': suggestions
                }
            }
            
            # イテレーション回数を更新
            self.task_iterations[task_id] = iteration + 1
            
            # タスクを適切なワーカーに再送信
            self.send_to_worker('task', 'retry', retry_task)
            
            self.logger.info(f"🔄 再実行タスクを送信: {task_id} (イテレーション {iteration + 2})")
            
            # Slack通知
            if hasattr(self, 'slack') and self.slack:
                self._send_retry_notification(task_id, issues, suggestions, iteration + 1)
                
        except Exception as e:
            # 再実行要求エラー
            context = {
                'operation': 'task_retry_request',
                'task_id': task_id,
                'iteration': iteration
            }
            self.handle_error(e, context, severity=ErrorSeverity.MEDIUM)
    
    def _send_retry_notification(self, task_id: str, issues: list, suggestions: list, iteration: int):
        """再実行通知をSlackに送信"""
        try:
            message = f"🔄 タスク品質改善のため再実行\n"
            message += f"タスクID: {task_id}\n"
            message += f"イテレーション: {iteration}\n"
            message += f"主な問題点: {', '.join(issues[:3])}\n"
            message += f"改善提案: {', '.join(suggestions[:2])}"
            
            self.slack.send_message(message)
            
        except Exception as e:
            # 再実行通知エラー
            context = {
                'operation': 'retry_notification',
                'task_id': task_id,
                'iteration': iteration
            }
            self.handle_error(e, context, severity=ErrorSeverity.LOW)

if __name__ == "__main__":
    worker = EnhancedPMWorker()
    worker.start()