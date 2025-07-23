"""プラグインシステム"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Plugin(ABC):
    """プラグインの基底クラス"""

    @property
    @abstractmethod
    def name(self) -> str:
        """プラグイン名"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """プラグインバージョン"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """プラグインの説明"""
        pass

    def on_load(self):
        """プラグインロード時"""
        pass

    def on_unload(self):
        """プラグインアンロード時"""
        pass


class PluginManager:
    """プラグインマネージャー"""

    def __init__(self):
        """初期化メソッド"""
        self.plugins: Dict[str, Plugin] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, plugin: Plugin):
        """プラグインを登録"""
        self.plugins[plugin.name] = plugin
        plugin.on_load()
        self.logger.info(f"Plugin loaded: {plugin.name} v{plugin.version}")

    def unregister(self, plugin_name: str):
        """プラグインを登録解除"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].on_unload()
            del self.plugins[plugin_name]
            self.logger.info(f"Plugin unloaded: {plugin_name}")

    def get_plugin(self, plugin_name: str) -> Plugin:
        """プラグインを取得"""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """登録されているプラグインのリスト"""
        return list(self.plugins.keys())


# グローバルインスタンス
plugin_manager = PluginManager()


# テスト用の実装（抽象メソッドエラーを回避）
class PerformanceLoggerPlugin(Plugin):
    """パフォーマンスログプラグイン"""

    @property
    def name(self) -> str:
        return "PerformanceLogger"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Log performance metrics"

    def log_performance(self, metric: str, value: float):
        """パフォーマンスメトリクスをログ"""
        print(f"[Performance] {metric}: {value}")
