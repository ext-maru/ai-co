#!/usr/bin/env python3
"""
プロンプトテンプレート機能をワーカーに統合するためのMixin
"""

from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


class PromptTemplateMixin:
    """ワーカーにプロンプトテンプレート機能を追加するMixin"""
    
    def __init__(self):
        """Mixin初期化"""
        self._prompt_manager = None
        self._worker_type = getattr(self, 'worker_type', 'unknown')
        self._default_template = 'default'
        
    @property
    def prompt_manager(self):
        """プロンプトマネージャーのシングルトンを取得（遅延インポート）"""
        if self._prompt_manager is None:
            # 循環インポートを避けるため、ここでインポート
            from libs.prompt_template_manager import PromptTemplateManager
            self._prompt_manager = PromptTemplateManager()
            if not self._prompt_manager.initialize():
                raise RuntimeError("Failed to initialize PromptTemplateManager")
        return self._prompt_manager
    
    def set_default_template(self, template_name: str):
        """デフォルトのテンプレート名を設定"""
        self._default_template = template_name
        if hasattr(self, 'logger'):
            self.logger.info(f"Default template set to: {template_name}")
    
    def generate_prompt(self, 
                       template_name: Optional[str] = None,
                       variables: Optional[Dict[str, Any]] = None,
                       include_rag: bool = True) -> Optional[str]:
        """プロンプトを生成"""
        template = template_name or self._default_template
        
        # ワーカー固有の変数を追加
        worker_vars = self._get_worker_variables()
        if variables:
            worker_vars.update(variables)
        
        return self.prompt_manager.generate_prompt(
            worker_type=self._worker_type,
            template_name=template,
            variables=worker_vars,
            include_rag=include_rag
        )
    
    def _get_worker_variables(self) -> Dict[str, Any]:
        """ワーカー固有の変数を取得（オーバーライド可能）"""
        return {
            'worker_type': self._worker_type,
            'worker_id': getattr(self, 'worker_id', 'unknown')
        }
    
    def create_custom_template(self, 
                              template_name: str,
                              template_content: str,
                              variables: List[str] = None,
                              description: str = None) -> bool:
        """カスタムテンプレートを作成"""
        return self.prompt_manager.create_template(
            worker_type=self._worker_type,
            template_name=template_name,
            template_content=template_content,
            variables=variables,
            description=description
        )
    
    def list_available_templates(self) -> List[Dict[str, Any]]:
        """利用可能なテンプレート一覧を取得"""
        templates = self.prompt_manager.list_templates(self._worker_type)
        return [t for t in templates if t['is_active']]
    
    def evaluate_last_prompt(self, task_id: str, score: float) -> bool:
        """最後に生成したプロンプトのパフォーマンスを評価"""
        return self.prompt_manager.evaluate_prompt_performance(task_id, score)


# 使用例：TaskWorkerへの統合
if __name__ == "__main__":
    from core import BaseWorker
    
    class EnhancedTaskWorker(BaseWorker, PromptTemplateMixin):
        def __init__(self):
            BaseWorker.__init__(self, worker_type='task')
            PromptTemplateMixin.__init__(self)
            
        def process_message(self, ch, method, properties, body):
            """メッセージ処理"""
            import json
            task = json.loads(body)
            
            # プロンプト生成
            prompt = self.generate_prompt(
                template_name='code_generation' if task.get('type') == 'code' else 'default',
                variables={
                    'task_id': task['id'],
                    'user_prompt': task['prompt'],
                    'language': task.get('language', 'Python')
                }
            )
            
            if prompt:
                self.logger.info(f"Generated prompt for task {task['id']}")
                # Claude実行など
                
            ch.basic_ack(delivery_tag=method.delivery_tag)
    
    # テスト
    worker = EnhancedTaskWorker()
    print("Available templates:")
    for template in worker.list_available_templates():
        print(f"- {template['template_name']} v{template['version']}")
