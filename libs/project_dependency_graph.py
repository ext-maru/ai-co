#!/usr/bin/env python3
"""
プロジェクト間依存関係管理システム（DAGベース）
エルダーズギルドのベストプラクティスに基づく実装
"""

import asyncio
import json
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

# import networkx as nx  # Optional for advanced graph analysis
# import matplotlib.pyplot as plt  # Optional for visualization
from concurrent.futures import ThreadPoolExecutor, as_completed

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
import sys

sys.path.insert(0, str(PROJECT_ROOT))


class DependencyType(Enum):
    """依存関係タイプ"""

    BUILD = "build"  # ビルド時依存
    RUNTIME = "runtime"  # 実行時依存
    TEST = "test"  # テスト時依存
    OPTIONAL = "optional"  # オプショナル依存


@dataclass
class ProjectNode:
    """プロジェクトノード"""

    id: str
    name: str
    path: Path
    type: str = "standard"  # standard, library, service, tool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dependency:
    """依存関係"""

    from_project: str
    to_project: str
    type: DependencyType
    version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CircularDependencyError(Exception):
    """循環依存エラー"""

    def __init__(self, cycle: List[str]):
        """初期化メソッド"""
        self.cycle = cycle
        super().__init__(f"循環依存を検出: {' -> '.join(cycle)} -> {cycle[0]}")


class ProjectDependencyGraph:
    """プロジェクト依存関係グラフ（エルダーズギルド仕様）"""

    def __init__(self):
        """初期化メソッド"""
        # グラフ構造
        self.nodes: Dict[str, ProjectNode] = {}
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self.dependencies: Dict[Tuple[str, str], Dependency] = {}

        # ログ設定（先に設定）
        self.logger = logging.getLogger("ProjectDependencyGraph")
        self.logger.setLevel(logging.INFO)

        # NetworkXグラフ（高度な分析用）
        self.nx_graph = None
        self.networkx_available = False
        self.logger.warning("NetworkX not available. Using built-in graph analysis.")

        # エルダーズギルドのベストプラクティス設定
        self.config = {
            "max_parallel_projects": 10,  # 最大並列実行数
            "cycle_detection": True,  # 循環依存検出
            "auto_resolve_versions": True,  # バージョン自動解決
            "cache_analysis": True,  # 分析結果キャッシュ
            "visualization": False,  # 可視化機能（matplotlibなしで無効化）
            "ai_optimization": True,  # AI最適化連携
        }

        # キャッシュ
        self._execution_order_cache = None
        self._critical_path_cache = None

        # 4賢者との連携準備
        self.sage_insights = {
            "task_sage": [],  # タスク実行順序の知見
            "knowledge_sage": [],  # 依存パターンの知識
            "incident_sage": [],  # 依存関係起因のインシデント
            "rag_sage": [],  # 他プロジェクトの成功パターン
        }

    def add_project(self, project: ProjectNode):
        """プロジェクトノード追加"""
        self.nodes[project.id] = project
        if self.networkx_available:
            self.nx_graph.add_node(project.id, **project.__dict__)
        self._invalidate_cache()

        self.logger.info(f"プロジェクト追加: {project.name} ({project.id})")

    def add_dependency(self, dependency: Dependency) -> bool:
        """依存関係追加（エルダーズギルドの品質チェック付き）"""
        from_id = dependency.from_project
        to_id = dependency.to_project

        # 自己依存チェック
        if from_id == to_id:
            self.logger.warning(f"自己依存をスキップ: {from_id}")
            return False

        # プロジェクト存在確認
        if from_id not in self.nodes or to_id not in self.nodes:
            self.logger.error(f"存在しないプロジェクト: {from_id} -> {to_id}")
            return False

        # 循環依存チェック（事前）
        if self.config["cycle_detection"]:
            if self._would_create_cycle(from_id, to_id):
                cycle = self._find_cycle_path(from_id, to_id)
                raise CircularDependencyError(cycle)

        # 依存関係登録
        self.graph[from_id].add(to_id)
        self.reverse_graph[to_id].add(from_id)
        self.dependencies[(from_id, to_id)] = dependency
        if self.networkx_available:
            self.nx_graph.add_edge(from_id, to_id, **dependency.__dict__)

        self._invalidate_cache()

        self.logger.info(
            f"依存関係追加: {from_id} -> {to_id} (type: {dependency.type.value})"
        )
        return True

    def _would_create_cycle(self, from_id: str, to_id: str) -> bool:
        """循環依存を作成するかチェック"""
        # DFSで到達可能性チェック
        visited = set()
        stack = [to_id]

        while stack:
            current = stack.pop()
            if current == from_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(self.graph.get(current, []))

        return False

    def _find_cycle_path(self, from_id: str, to_id: str) -> List[str]:
        """循環パスを見つける"""
        # 簡易実装（詳細な経路探索）
        path = [from_id]
        current = to_id

        while current != from_id:
            path.append(current)
            # 次のノードを探す
            for next_node in self.graph.get(current, []):
                if next_node in path or next_node == from_id:
                    path.append(next_node)
                    return path
            current = (
                list(self.graph.get(current, []))[0]
                if self.graph.get(current)
                else current
            )

        return path

    def get_execution_order(self) -> List[List[str]]:
        """実行順序を取得（並列実行可能なレベルごと）"""
        if self._execution_order_cache is not None:
            return self._execution_order_cache

        # カーンのアルゴリズム（レベル付きトポロジカルソート）
        in_degree = defaultdict(int)

        # 入次数計算
        for node in self.nodes:
            for dependent in self.graph.get(node, []):
                in_degree[dependent] += 1

        # 入次数0のノードから開始
        current_level = [node for node in self.nodes if in_degree[node] == 0]
        levels = []
        processed = set()

        while current_level:
            levels.append(current_level[:])
            next_level = []

            for node in current_level:
                processed.add(node)
                for dependent in self.graph.get(node, []):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_level.append(dependent)

            current_level = next_level

        # 全ノードが処理されたかチェック
        if len(processed) != len(self.nodes):
            unprocessed = set(self.nodes.keys()) - processed
            self.logger.error(f"循環依存の可能性: {unprocessed}")

        self._execution_order_cache = levels
        return levels

    def get_parallel_groups(self) -> List[Dict[str, Any]]:
        """並列実行グループを詳細情報付きで取得"""
        levels = self.get_execution_order()
        groups = []

        for i, level in enumerate(levels):
            group = {
                "level": i + 1,
                "projects": level,
                "can_parallel": True,
                "estimated_time": self._estimate_level_time(level),
                "dependencies_from_previous": self._get_dependencies_from_previous(
                    level, i
                ),
            }
            groups.append(group)

        return groups

    def _estimate_level_time(self, level: List[str]) -> float:
        """レベルの推定実行時間（並列実行を考慮）"""
        if not level:
            return 0.0

        # 各プロジェクトの推定時間（メタデータから取得）
        times = []
        for project_id in level:
            project = self.nodes.get(project_id)
            if project and "estimated_minutes" in project.metadata:
                times.append(project.metadata["estimated_minutes"])
            else:
                times.append(10.0)  # デフォルト10分

        # 並列実行時は最大時間
        return max(times)

    def _get_dependencies_from_previous(
        self, level: List[str], level_index: int
    ) -> Dict[str, List[str]]:
        """前レベルからの依存関係"""
        deps = {}
        if level_index == 0:
            return deps

        for project_id in level:
            deps[project_id] = list(self.reverse_graph.get(project_id, []))

        return deps

    def find_critical_path(self) -> List[str]:
        """クリティカルパスを見つける"""
        if self._critical_path_cache is not None:
            return self._critical_path_cache

        if (
            not self.networkx_available
            or not self.nx_graph
            or not self.nx_graph.nodes()
        ):
            # NetworkXなしでクリティカルパス計算（簡易版）
            return self._calculate_critical_path_simple()

        # 重み付けを追加（推定時間）
        for node in self.nx_graph.nodes():
            project = self.nodes.get(node)
            weight = project.metadata.get("estimated_minutes", 10) if project else 10
            self.nx_graph.nodes[node]["weight"] = weight

        # DAGの最長パスを見つける
        try:
            import networkx as nx

            critical_path = nx.dag_longest_path(self.nx_graph, weight="weight")
            self._critical_path_cache = critical_path
            return critical_path
        except Exception as e:
            self.logger.error(f"NetworkX critical path calculation failed: {e}")
            return self._calculate_critical_path_simple()

    def analyze_impact(self, project_id: str) -> Dict[str, Any]:
        """プロジェクト変更の影響分析"""
        if project_id not in self.nodes:
            return {"error": "プロジェクトが存在しません"}

        # 直接影響を受けるプロジェクト
        direct_impact = list(self.reverse_graph.get(project_id, []))

        # 間接的な影響（推移的閉包）
        all_impacted = set()
        queue = deque(direct_impact)

        while queue:
            current = queue.popleft()
            if current not in all_impacted:
                all_impacted.add(current)
                queue.extend(self.reverse_graph.get(current, []))

        return {
            "project": project_id,
            "direct_impact": direct_impact,
            "total_impacted": list(all_impacted),
            "impact_count": len(all_impacted),
            "critical_path_member": project_id in self.find_critical_path(),
            "rebuild_required": list(all_impacted),
        }

    def optimize_with_ai(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """AI最適化との連携（エルダーズギルドのベストプラクティス）"""
        optimization_result = {
            "original_levels": self.get_execution_order(),
            "optimized_levels": [],
            "improvements": [],
            "sage_recommendations": {},
        }

        # タスク賢者の知見を活用
        task_sage_insight = {
            "parallel_efficiency": self._calculate_parallel_efficiency(),
            "bottlenecks": self._identify_bottlenecks(),
            "optimization_potential": self._calculate_optimization_potential(),
        }

        optimization_result["sage_recommendations"]["task_sage"] = task_sage_insight

        # ナレッジ賢者のパターン認識
        knowledge_sage_insight = {
            "common_patterns": self._identify_dependency_patterns(),
            "anti_patterns": self._detect_anti_patterns(),
            "best_practices": self._suggest_best_practices(),
        }

        optimization_result["sage_recommendations"][
            "knowledge_sage"
        ] = knowledge_sage_insight

        # 最適化提案
        if task_sage_insight["optimization_potential"] > 0.2:
            optimization_result["improvements"].append(
                {
                    "type": "parallel_optimization",
                    "description": "並列実行の最適化により20%以上の改善が見込めます",
                    "action": "プロジェクト分割を検討してください",
                }
            )

        return optimization_result

    def _calculate_parallel_efficiency(self) -> float:
        """並列実行効率の計算"""
        levels = self.get_execution_order()
        if not levels:
            return 0.0

        total_projects = len(self.nodes)
        level_count = len(levels)

        # 理想的な並列実行との比較
        ideal_levels = max(1, total_projects // self.config["max_parallel_projects"])
        efficiency = ideal_levels / level_count if level_count > 0 else 0

        return min(1.0, efficiency)

    def _identify_bottlenecks(self) -> List[str]:
        """ボトルネックプロジェクトの特定"""
        bottlenecks = []

        # 多くのプロジェクトが依存しているノード
        for node in self.nodes:
            dependent_count = len(self.reverse_graph.get(node, []))
            if dependent_count >= 3:  # 3つ以上のプロジェクトが依存
                bottlenecks.append(node)

        return bottlenecks

    def _calculate_optimization_potential(self) -> float:
        """最適化可能性の計算"""
        current_efficiency = self._calculate_parallel_efficiency()

        # ボトルネックの影響を計算
        bottlenecks = self._identify_bottlenecks()
        bottleneck_impact = len(bottlenecks) / len(self.nodes) if self.nodes else 0

        # 最適化可能性 = 1 - 現在の効率 - ボトルネックの影響
        potential = max(0, 1 - current_efficiency - bottleneck_impact)

        return potential

    def _identify_dependency_patterns(self) -> List[Dict[str, Any]]:
        """依存関係パターンの識別"""
        patterns = []

        # レイヤードアーキテクチャパターン
        if self._has_layered_pattern():
            patterns.append(
                {
                    "type": "layered_architecture",
                    "description": "レイヤードアーキテクチャパターンを検出",
                    "quality": "good",
                }
            )

        # スター型依存パターン
        star_centers = self._find_star_patterns()
        if star_centers:
            patterns.append(
                {
                    "type": "star_dependency",
                    "description": f"スター型依存パターンを検出: {star_centers}",
                    "quality": "warning",
                    "recommendation": "共通ライブラリの分割を検討",
                }
            )

        return patterns

    def _detect_anti_patterns(self) -> List[Dict[str, Any]]:
        """アンチパターンの検出"""
        anti_patterns = []

        # 相互依存の検出
        mutual_deps = self._find_mutual_dependencies()
        if mutual_deps:
            anti_patterns.append(
                {
                    "type": "mutual_dependency",
                    "description": f"相互依存を検出: {mutual_deps}",
                    "severity": "high",
                    "recommendation": "インターフェース分離を検討",
                }
            )

        # 深い依存階層
        max_depth = self._calculate_max_dependency_depth()
        if max_depth > 5:
            anti_patterns.append(
                {
                    "type": "deep_hierarchy",
                    "description": f"依存階層が深すぎます（{max_depth}層）",
                    "severity": "medium",
                    "recommendation": "中間層の統合を検討",
                }
            )

        return anti_patterns

    def _suggest_best_practices(self) -> List[str]:
        """ベストプラクティスの提案"""
        suggestions = []

        # エルダーズギルドのベストプラクティス
        suggestions.append("🏛️ 各プロジェクトは独立してテスト可能にする")
        suggestions.append("🔄 循環依存は絶対に避ける")
        suggestions.append("📦 共通機能は独立したライブラリとして分離")
        suggestions.append("🎯 クリティカルパスの最小化を意識")
        suggestions.append("⚡ 並列実行可能な構造を維持")

        return suggestions

    def _has_layered_pattern(self) -> bool:
        """レイヤードパターンの検出"""
        levels = self.get_execution_order()
        # 各レベルのプロジェクトタイプをチェック
        # 簡易的な実装
        return len(levels) >= 3

    def _find_star_patterns(self) -> List[str]:
        """スター型パターンの中心を見つける"""
        star_centers = []
        threshold = 5  # 5つ以上のプロジェクトから依存されている

        for node in self.nodes:
            if len(self.reverse_graph.get(node, [])) >= threshold:
                star_centers.append(node)

        return star_centers

    def _find_mutual_dependencies(self) -> List[Tuple[str, str]]:
        """相互依存を見つける（本来は避けるべき）"""
        mutual = []
        checked = set()

        for node in self.nodes:
            for dependent in self.graph.get(node, []):
                if (dependent, node) not in checked and node in self.graph.get(
                    dependent, []
                ):
                    mutual.append((node, dependent))
                    checked.add((node, dependent))
                    checked.add((dependent, node))

        return mutual

    def _calculate_max_dependency_depth(self) -> int:
        """最大依存深度の計算"""
        if not self.nodes:
            return 0

        levels = self.get_execution_order()
        return len(levels)

    def _calculate_critical_path_simple(self) -> List[str]:
        """NetworkXなしの簡易クリティカルパス計算"""
        if not self.nodes:
            return []

        # 実行順序レベルから最長パスを推定
        levels = self.get_execution_order()
        if not levels:
            return []

        # 各レベルから最も重いノードを選択
        critical_path = []
        for level in levels:
            if level:
                # 推定時間で最も重いプロジェクトを選択
                heaviest_project = max(
                    level,
                    key=lambda p: self.nodes.get(
                        p,
                        type("obj", (object,), {"metadata": {"estimated_minutes": 10}}),
                    ).metadata.get("estimated_minutes", 10),
                )
                critical_path.append(heaviest_project)

        return critical_path

    def visualize(
        self, output_path: Optional[Path] = None, layout: str = "hierarchical"
    ):
        """依存関係グラフの可視化（エルダーズギルド仕様）"""
        if not self.config["visualization"]:
            return

        try:
            import matplotlib.pyplot as plt
        except ImportError:
            self.logger.warning("matplotlib not installed. Skipping visualization.")
            return

        plt.figure(figsize=(12, 8))

        # レイアウト選択
        if layout == "hierarchical":
            # 階層的レイアウト（レベルごと）
            levels = self.get_execution_order()
            pos = {}
            y_offset = 0

            for level_idx, level in enumerate(levels):
                x_offset = -(len(level) - 1) / 2
                for proj_idx, project in enumerate(level):
                    pos[project] = (x_offset + proj_idx, -y_offset)
                y_offset += 1
        else:
            # 自動レイアウト
            import networkx as nx

            pos = nx.spring_layout(self.nx_graph)

        # ノードの色分け
        node_colors = []
        for node in self.nx_graph.nodes():
            project = self.nodes.get(node)
            if project:
                if project.type == "library":
                    node_colors.append("lightblue")
                elif project.type == "service":
                    node_colors.append("lightgreen")
                elif project.type == "tool":
                    node_colors.append("lightyellow")
                else:
                    node_colors.append("lightgray")
            else:
                node_colors.append("white")

        # グラフ描画
        import networkx as nx

        nx.draw(
            self.nx_graph,
            pos,
            node_color=node_colors,
            node_size=3000,
            font_size=10,
            font_weight="bold",
            arrows=True,
            edge_color="gray",
            arrowsize=20,
            with_labels=True,
        )

        # クリティカルパスを強調
        critical_path = self.find_critical_path()
        if len(critical_path) > 1:
            critical_edges = [
                (critical_path[i], critical_path[i + 1])
                for i in range(len(critical_path) - 1)
            ]
            nx.draw_networkx_edges(
                self.nx_graph,
                pos,
                edgelist=critical_edges,
                edge_color="red",
                width=3,
                arrows=True,
                arrowsize=25,
            )

        plt.title(
            "🏛️ エルダーズギルド プロジェクト依存関係グラフ",
            fontsize=16,
            fontweight="bold",
        )

        # 凡例
        try:
            from matplotlib.patches import Patch
        except ImportError:
            self.logger.warning("matplotlib.patches not available. Skipping legend.")
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches="tight")
                self.logger.info(f"グラフを保存: {output_path}")
            else:
                plt.show()
            plt.close()
            return
        legend_elements = [
            Patch(facecolor="lightblue", label="ライブラリ"),
            Patch(facecolor="lightgreen", label="サービス"),
            Patch(facecolor="lightyellow", label="ツール"),
            Patch(facecolor="lightgray", label="標準"),
            Patch(facecolor="red", label="クリティカルパス"),
        ]
        plt.legend(handles=legend_elements, loc="upper right")

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            self.logger.info(f"グラフを保存: {output_path}")
        else:
            plt.show()

        plt.close()

    def export_mermaid(self) -> str:
        """Mermaid形式でエクスポート"""
        mermaid = ["graph TD"]

        # スタイル定義
        mermaid.append(
            "    classDef library fill:#add8e6,stroke:#333,stroke-width:2px;"
        )
        mermaid.append(
            "    classDef service fill:#90ee90,stroke:#333,stroke-width:2px;"
        )
        mermaid.append("    classDef tool fill:#ffffe0,stroke:#333,stroke-width:2px;")
        mermaid.append(
            "    classDef critical fill:#ff6b6b,stroke:#333,stroke-width:3px;"
        )

        # ノード定義
        for node_id, node in self.nodes.items():
            label = f"{node.name}"
            mermaid.append(f"    {node_id}[{label}]")

            # クラス適用
            if node.type == "library":
                mermaid.append(f"    class {node_id} library")
            elif node.type == "service":
                mermaid.append(f"    class {node_id} service")
            elif node.type == "tool":
                mermaid.append(f"    class {node_id} tool")

        # エッジ定義
        for (from_id, to_id), dep in self.dependencies.items():
            arrow = "-->"
            if dep.type == DependencyType.OPTIONAL:
                arrow = "-.->"
            label = f"|{dep.type.value}|" if dep.type != DependencyType.BUILD else ""
            mermaid.append(f"    {from_id} {arrow}{label} {to_id}")

        # クリティカルパス強調
        critical_path = self.find_critical_path()
        for node in critical_path:
            mermaid.append(f"    class {node} critical")

        return "\n".join(mermaid)

    def _invalidate_cache(self):
        """キャッシュ無効化"""
        self._execution_order_cache = None
        self._critical_path_cache = None

    def save_state(self, file_path: Path):
        """状態を保存"""
        state = {
            "nodes": {k: v.__dict__ for k, v in self.nodes.items()},
            "dependencies": [
                {
                    "from": dep.from_project,
                    "to": dep.to_project,
                    "type": dep.type.value,
                    "version": dep.version,
                    "metadata": dep.metadata,
                }
                for dep in self.dependencies.values()
            ],
            "sage_insights": self.sage_insights,
            "timestamp": datetime.now().isoformat(),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False, default=str)

    def load_state(self, file_path: Path):
        """状態を読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            state = json.load(f)

        # ノード復元
        for node_id, node_data in state["nodes"].items():
            node = ProjectNode(
                id=node_data["id"],
                name=node_data["name"],
                path=Path(node_data["path"]),
                type=node_data.get("type", "standard"),
                metadata=node_data.get("metadata", {}),
            )
            self.add_project(node)

        # 依存関係復元
        for dep_data in state["dependencies"]:
            dep = Dependency(
                from_project=dep_data["from"],
                to_project=dep_data["to"],
                type=DependencyType(dep_data["type"]),
                version=dep_data.get("version"),
                metadata=dep_data.get("metadata", {}),
            )
            self.add_dependency(dep)

        # 賢者の知見復元
        self.sage_insights = state.get("sage_insights", self.sage_insights)


# デモ実行
def demo():
    """デモ実行"""
    graph = ProjectDependencyGraph()

    # プロジェクト定義
    projects = [
        ProjectNode(
            "frontend",
            "フロントエンド",
            Path("frontend"),
            "service",
            {"estimated_minutes": 30},
        ),
        ProjectNode("api", "API", Path("api"), "service", {"estimated_minutes": 20}),
        ProjectNode(
            "database",
            "データベース",
            Path("database"),
            "service",
            {"estimated_minutes": 10},
        ),
        ProjectNode(
            "auth-lib",
            "認証ライブラリ",
            Path("libs/auth"),
            "library",
            {"estimated_minutes": 15},
        ),
        ProjectNode(
            "monitoring",
            "監視ツール",
            Path("monitoring"),
            "tool",
            {"estimated_minutes": 25},
        ),
        ProjectNode(
            "common-lib",
            "共通ライブラリ",
            Path("libs/common"),
            "library",
            {"estimated_minutes": 5},
        ),
    ]

    # プロジェクト追加
    for project in projects:
        graph.add_project(project)

    # 依存関係定義
    dependencies = [
        Dependency("frontend", "api", DependencyType.RUNTIME),
        Dependency("frontend", "auth-lib", DependencyType.BUILD),
        Dependency("api", "database", DependencyType.RUNTIME),
        Dependency("api", "auth-lib", DependencyType.BUILD),
        Dependency("api", "common-lib", DependencyType.BUILD),
        Dependency("auth-lib", "common-lib", DependencyType.BUILD),
        Dependency("monitoring", "api", DependencyType.RUNTIME, version="optional"),
    ]

    # 依存関係追加
    for dep in dependencies:
        try:
            graph.add_dependency(dep)
        except CircularDependencyError as e:
            print(f"❌ エラー: {e}")

    # 実行順序の取得
    print("🏛️ エルダーズギルド プロジェクト依存関係分析")
    print("=" * 60)

    print("\n📊 並列実行可能グループ:")
    groups = graph.get_parallel_groups()
    for group in groups:
        print(f"\nLevel {group['level']}: {group['projects']}")
        print(f"  推定時間: {group['estimated_time']}分（並列実行）")
        if group["dependencies_from_previous"]:
            print(f"  依存元: {group['dependencies_from_previous']}")

    # クリティカルパス
    critical_path = graph.find_critical_path()
    print(f"\n🎯 クリティカルパス: {' -> '.join(critical_path)}")

    # 影響分析
    print("\n📈 影響分析（common-libを変更した場合）:")
    impact = graph.analyze_impact("common-lib")
    print(f"  直接影響: {impact['direct_impact']}")
    print(f"  全影響範囲: {impact['total_impacted']}")
    print(f"  再ビルド必要: {impact['rebuild_required']}")

    # AI最適化提案
    print("\n🤖 AI最適化提案:")
    optimization = graph.optimize_with_ai({})
    print(
        f"  並列実行効率: {optimization['sage_recommendations']['task_sage']['parallel_efficiency']:.1%}"
    )
    print(
        f"  ボトルネック: {optimization['sage_recommendations']['task_sage']['bottlenecks']}"
    )

    # Mermaid出力
    print("\n📝 Mermaid図:")
    print(graph.export_mermaid())

    # 可視化（オプション）
    # graph.visualize(Path("dependency_graph.png"))


if __name__ == "__main__":
    demo()
