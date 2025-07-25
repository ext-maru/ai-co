"""
Template Registry - エルダーズギルド テンプレート管理システム

コードテンプレート、ドキュメントテンプレート、設定テンプレートの
中央管理システム
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """テンプレート登録・管理システム"""
    
    def __init__(self, template_dir: str = "templates"):
        """初期化メソッド"""
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)
        self.templates = {}
        self._load_templates()
        
    def _load_templates(self):
        """テンプレートファイルを読み込み"""
        try:
            for template_file in self.template_dir.glob("*.json"):
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    self.templates[template_file.stem] = template_data
                    
            logger.info(f"Loaded {len(self.templates)} templates")
        except Exception as e:
            logger.warning(f"Template loading error: {e}")
    
    def register_template(self, name: str, template: Dict[str, Any]) -> bool:
        """テンプレートを登録"""
        try:
            self.templates[name] = {
                **template,
                "registered_at": datetime.now().isoformat()
            }
            
            # ファイルに保存
            template_file = self.template_dir / f"{name}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates[name], f, ensure_ascii=False, indent=2)
                
            logger.info(f"Template '{name}' registered successfully")
            return True
        except Exception as e:
            logger.error(f"Template registration failed: {e}")
            return False
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """テンプレートを取得"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """登録済みテンプレート一覧"""
        return list(self.templates.keys())


# デフォルトインスタンス
default_registry = TemplateRegistry()

def register_template(name: str, template: Dict[str, Any]) -> bool:
    """テンプレート登録（グローバル関数）"""
    return default_registry.register_template(name, template)

def get_template(name: str) -> Optional[Dict[str, Any]]:
    """テンプレート取得（グローバル関数）"""
    return default_registry.get_template(name)
