#!/usr/bin/env python3
"""
🔮 Causality Control System
因果律制御システム

Elder Flow Phase 12: 因果関係の直接操作と制御
"""

import asyncio
import numpy as np
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
# networkx は optional import
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
import itertools
from collections import defaultdict, deque

class CausalityType(Enum):
    """因果律タイプ"""
    DETERMINISTIC = "deterministic"  # 決定論的
    PROBABILISTIC = "probabilistic"  # 確率的
    QUANTUM = "quantum"  # 量子的
    TEMPORAL = "temporal"  # 時間的
    SPATIAL = "spatial"  # 空間的
    MULTIDIMENSIONAL = "multidimensional"  # 多次元的

class CausalDirection(Enum):
    """因果方向"""
    FORWARD = "forward"  # 順方向
    BACKWARD = "backward"  # 逆方向
    BIDIRECTIONAL = "bidirectional"  # 双方向
    ACAUSAL = "acausal"  # 非因果
    SUPERPOSITION = "superposition"  # 重ね合わせ

class EventType(Enum):
    """イベントタイプ"""
    CAUSE = "cause"  # 原因
    EFFECT = "effect"  # 結果
    CATALYST = "catalyst"  # 触媒
    OBSERVER = "observer"  # 観測者
    QUANTUM_STATE = "quantum_state"  # 量子状態

@dataclass
class CausalEvent:
    """因果イベント"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    probability: float = 1.0
    causality_strength: float = 1.0
    quantum_state: Optional[str] = None
    dimensions: List[int] = field(default_factory=lambda: [3, 4])  # デフォルト3D+時間

@dataclass
class CausalLink:
    """因果リンク"""
    link_id: str
    cause_event_id: str
    effect_event_id: str
    causality_type: CausalityType
    direction: CausalDirection
    strength: float
    delay: float  # 秒単位
    confidence: float
    quantum_entangled: bool = False
    created_at: datetime = field(default_factory=datetime.now)

class SimpleDirectedGraph:
    """Simple directed graph implementation for when networkx is not available"""

    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(list)

    def add_node(self, node_id, **attributes):
        self.nodes[node_id] = attributes

    def add_edge(self, source, target, **attributes):
        self.edges[source].append((target, attributes))

    def number_of_nodes(self):
        return len(self.nodes)

    def number_of_edges(self):
        return sum(len(targets) for targets in self.edges.values())

    def successors(self, node):
        return [target for target, _ in self.edges.get(node, [])]

    def predecessors(self, node):
        predecessors = []
        for source, targets in self.edges.items():
            for target, _ in targets:
                if target == node:
                    predecessors.append(source)
        return predecessors

    def __contains__(self, node):
        return node in self.nodes

    def __getitem__(self, source):
        """Return edge data structure for networkx compatibility"""
        result = {}
        for target, attributes in self.edges.get(source, []):
            result[target] = attributes
        return result

class CausalityGraph:
    """因果律グラフ"""

    def __init__(self):
        self.graph = SimpleDirectedGraph()  # カスタム実装を常に使用
        self.events = {}
        self.links = {}
        self.quantum_states = {}
        self.timeline_branches = {}

    def add_event(self, event: CausalEvent):
        """イベント追加"""
        self.events[event.event_id] = event
        self.graph.add_node(event.event_id,
                           timestamp=event.timestamp,
                           event_type=event.event_type.value,
                           probability=event.probability)

    def add_causal_link(self, link: CausalLink):
        """因果リンク追加"""
        self.links[link.link_id] = link

        # グラフにエッジ追加
        self.graph.add_edge(link.cause_event_id, link.effect_event_id,
                           link_id=link.link_id,
                           strength=link.strength,
                           delay=link.delay,
                           confidence=link.confidence,
                           causality_type=link.causality_type.value)

    def detect_causal_loops(self) -> List[List[str]]:
        """因果ループ検出"""
        # Simple cycle detection using DFS
        return self._detect_cycles_dfs()

    def _detect_cycles_dfs(self) -> List[List[str]]:
        """DFSを使った簡易サイクル検出"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            if node in rec_stack:
                # サイクル発見
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for successor in self.graph.successors(node):
                dfs(successor, path.copy())

            rec_stack.remove(node)

        for node in self.graph.nodes:
            if node not in visited:
                dfs(node, [])

        return cycles

    def calculate_causal_influence(self, event_id: str, depth: int = 3) -> Dict[str, float]:
        """因果影響度計算"""
        influence_map = {}

        if event_id not in self.graph:
            return influence_map

        # 深度優先探索で影響を計算
        visited = set()
        stack = [(event_id, 1.0, 0)]  # (event_id, influence, depth)

        while stack:
            current_id, current_influence, current_depth = stack.pop()

            if current_id in visited or current_depth > depth:
                continue

            visited.add(current_id)
            influence_map[current_id] = influence_map.get(current_id, 0) + current_influence

            # 隣接ノードに伝播
            for neighbor in self.graph.successors(current_id):
                edge_data = self.graph[current_id][neighbor]
                strength = edge_data.get('strength', 0.5)
                confidence = edge_data.get('confidence', 0.5)

                # 影響度は強度と信頼度の積で減衰
                next_influence = current_influence * strength * confidence * 0.8

                if next_influence > 0.01:  # 閾値以上の場合のみ継続
                    stack.append((neighbor, next_influence, current_depth + 1))

        return influence_map

    def find_causal_path(self, source: str, target: str) -> Optional[List[str]]:
        """因果パス検索"""
        return self._find_path_bfs(source, target)

    def _find_path_bfs(self, source: str, target: str) -> Optional[List[str]]:
        """BFSを使った最短パス検索"""
        if source not in self.graph or target not in self.graph:
            return None

        queue = deque([(source, [source])])
        visited = {source}

        while queue:
            current, path = queue.popleft()

            if current == target:
                return path

            for successor in self.graph.successors(current):
                if successor not in visited:
                    visited.add(successor)
                    queue.append((successor, path + [successor]))

        return None

    def get_temporal_ordering(self) -> List[str]:
        """時間順序取得"""
        events_with_time = [(event_id, self.events[event_id].timestamp)
                           for event_id in self.events.keys()]
        events_with_time.sort(key=lambda x: x[1])
        return [event_id for event_id, _ in events_with_time]

class QuantumCausalityEngine:
    """量子因果律エンジン"""

    def __init__(self):
        self.quantum_states = {}
        self.entanglement_pairs = {}
        self.superposition_events = {}
        self.measurement_history = []

    async def create_quantum_causal_event(self, event_data: Dict[str, Any]) -> CausalEvent:
        """量子因果イベント作成"""
        event_id = f"quantum_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # 量子状態の初期化
        quantum_state = self._initialize_quantum_state()

        event = CausalEvent(
            event_id=event_id,
            event_type=EventType.QUANTUM_STATE,
            timestamp=datetime.now(),
            data=event_data,
            probability=self._calculate_quantum_probability(quantum_state),
            quantum_state=quantum_state
        )

        self.quantum_states[event_id] = quantum_state
        return event

    def _initialize_quantum_state(self) -> str:
        """量子状態初期化"""
        # 基底状態のランダム重ね合わせ
        alpha = np.random.random() + 1j * np.random.random()
        beta = np.random.random() + 1j * np.random.random()

        # 正規化
        norm = np.sqrt(abs(alpha)**2 + abs(beta)**2)
        alpha /= norm
        beta /= norm

        return f"|ψ⟩ = {alpha:.3f}|0⟩ + {beta:.3f}|1⟩"

    def _calculate_quantum_probability(self, quantum_state: str) -> float:
        """量子確率計算"""
        # 量子状態からの確率抽出（簡易版）
        try:
            # 状態文字列から振幅を抽出
            parts = quantum_state.split('|0⟩ + ')
            if len(parts) == 2:
                alpha_str = parts[0].split(' = ')[1]
                beta_str = parts[1].split('|1⟩')[0]

                # 複素数として解析
                alpha = complex(alpha_str.replace('j', 'j'))
                probability = abs(alpha)**2
                return min(max(probability, 0.0), 1.0)
        except:
            pass

        return 0.5  # デフォルト確率

    async def entangle_events(self, event1_id: str, event2_id: str) -> str:
        """イベント量子もつれ"""
        entanglement_id = f"entangle_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # もつれ状態生成
        entangled_state = self._create_entangled_state()

        self.entanglement_pairs[entanglement_id] = {
            "event1": event1_id,
            "event2": event2_id,
            "state": entangled_state,
            "created_at": datetime.now(),
            "correlation_strength": np.random.uniform(0.7, 1.0)
        }

        return entanglement_id

    def _create_entangled_state(self) -> str:
        """もつれ状態生成"""
        # ベル状態の一つを生成
        states = [
            "|Φ+⟩ = (|00⟩ + |11⟩)/√2",
            "|Φ-⟩ = (|00⟩ - |11⟩)/√2",
            "|Ψ+⟩ = (|01⟩ + |10⟩)/√2",
            "|Ψ-⟩ = (|01⟩ - |10⟩)/√2"
        ]
        return np.random.choice(states)

    async def measure_quantum_causality(self, event_id: str) -> Dict[str, Any]:
        """量子因果律測定"""
        if event_id not in self.quantum_states:
            return {"error": "Event not found in quantum states"}

        # 測定による状態の崩壊
        measurement_result = np.random.choice([0, 1])
        collapsed_state = f"|{measurement_result}⟩"

        measurement_record = {
            "event_id": event_id,
            "original_state": self.quantum_states[event_id],
            "collapsed_state": collapsed_state,
            "measurement_result": measurement_result,
            "measurement_time": datetime.now(),
            "causality_impact": self._calculate_causality_impact(measurement_result)
        }

        self.measurement_history.append(measurement_record)
        self.quantum_states[event_id] = collapsed_state

        return measurement_record

    def _calculate_causality_impact(self, measurement: int) -> float:
        """因果律への影響計算"""
        # 測定結果による因果律への影響度
        base_impact = 0.1 if measurement == 0 else 0.15
        quantum_uncertainty = np.random.normal(0, 0.05)
        return max(0.0, min(1.0, base_impact + quantum_uncertainty))

class TemporalCausalityController:
    """時間因果律制御器"""

    def __init__(self):
        self.temporal_locks = {}
        self.causality_buffers = {}
        self.timeline_branches = {}
        self.paradox_detectors = []

    async def create_temporal_lock(self, event_id: str, lock_duration: float) -> str:
        """時間ロック作成"""
        lock_id = f"lock_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        lock = {
            "lock_id": lock_id,
            "event_id": event_id,
            "locked_at": datetime.now(),
            "duration": lock_duration,
            "expires_at": datetime.now() + timedelta(seconds=lock_duration),
            "lock_strength": np.random.uniform(0.8, 1.0)
        }

        self.temporal_locks[lock_id] = lock

        # 自動解除タイマー
        asyncio.create_task(self._auto_release_lock(lock_id, lock_duration))

        return lock_id

    async def _auto_release_lock(self, lock_id: str, duration: float):
        """自動ロック解除"""
        await asyncio.sleep(duration)
        if lock_id in self.temporal_locks:
            del self.temporal_locks[lock_id]

    async def create_causality_buffer(self, buffer_size: int = 100) -> str:
        """因果律バッファ作成"""
        buffer_id = f"buffer_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        buffer = {
            "buffer_id": buffer_id,
            "size": buffer_size,
            "events": deque(maxlen=buffer_size),
            "created_at": datetime.now(),
            "overflow_count": 0
        }

        self.causality_buffers[buffer_id] = buffer
        return buffer_id

    async def detect_temporal_paradox(self, causal_graph: CausalityGraph) -> Dict[str, Any]:
        """時間的逆説検出"""
        paradoxes = []

        # 因果ループ検出
        loops = causal_graph.detect_causal_loops()
        for loop in loops:
            if len(loop) > 1:
                paradoxes.append({
                    "type": "causal_loop",
                    "events": loop,
                    "severity": len(loop) * 0.2,
                    "description": f"Causal loop detected with {len(loop)} events"
                })

        # 時間順序矛盾検出
        temporal_order = causal_graph.get_temporal_ordering()
        for i, event_id in enumerate(temporal_order):
            if event_id in causal_graph.graph:
                # 未来のイベントが過去のイベントに影響を与えていないかチェック
                for predecessor in causal_graph.graph.predecessors(event_id):
                    pred_index = temporal_order.index(predecessor) if predecessor in temporal_order else -1
                    if pred_index > i:
                        paradoxes.append({
                            "type": "temporal_violation",
                            "cause": predecessor,
                            "effect": event_id,
                            "severity": 0.8,
                            "description": "Future event causing past event"
                        })

        return {
            "paradoxes_detected": len(paradoxes),
            "paradoxes": paradoxes,
            "timeline_stability": max(0.0, 1.0 - len(paradoxes) * 0.1),
            "recommended_action": "resolve_paradoxes" if paradoxes else "continue"
        }

class CausalityControlSystem:
    """因果律制御統合システム"""

    def __init__(self):
        self.causal_graph = CausalityGraph()
        self.quantum_engine = QuantumCausalityEngine()
        self.temporal_controller = TemporalCausalityController()
        self.operation_history = []
        self.system_stats = {
            "total_events": 0,
            "total_links": 0,
            "quantum_events": 0,
            "paradoxes_resolved": 0,
            "timeline_integrity": 1.0
        }

    async def create_causal_event(self, event_data: Dict[str, Any], event_type: EventType = EventType.CAUSE) -> str:
        """因果イベント作成"""
        if event_type == EventType.QUANTUM_STATE:
            event = await self.quantum_engine.create_quantum_causal_event(event_data)
            self.system_stats["quantum_events"] += 1
        else:
            event_id = f"event_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            event = CausalEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(),
                data=event_data
            )

        self.causal_graph.add_event(event)
        self.system_stats["total_events"] += 1

        return event.event_id

    async def establish_causality(self, cause_id: str, effect_id: str,
                                causality_type: CausalityType = CausalityType.DETERMINISTIC,
                                strength: float = 1.0) -> str:
        """因果関係確立"""
        link_id = f"link_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        link = CausalLink(
            link_id=link_id,
            cause_event_id=cause_id,
            effect_event_id=effect_id,
            causality_type=causality_type,
            direction=CausalDirection.FORWARD,
            strength=strength,
            delay=np.random.uniform(0.01, 1.0),  # ランダム遅延
            confidence=np.random.uniform(0.8, 1.0)
        )

        self.causal_graph.add_causal_link(link)
        self.system_stats["total_links"] += 1

        return link_id

    async def manipulate_causality(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """因果律操作"""
        operation_type = operation.get("type")
        parameters = operation.get("parameters", {})

        start_time = datetime.now()

        try:
            if operation_type == "reverse_causality":
                result = await self._reverse_causality(parameters)
            elif operation_type == "amplify_causality":
                result = await self._amplify_causality(parameters)
            elif operation_type == "create_quantum_entanglement":
                result = await self._create_quantum_entanglement(parameters)
            elif operation_type == "temporal_isolation":
                result = await self._temporal_isolation(parameters)
            elif operation_type == "causality_dampening":
                result = await self._causality_dampening(parameters)
            else:
                raise ValueError(f"Unknown causality operation: {operation_type}")

            operation_record = {
                "operation": operation,
                "result": result,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": start_time.isoformat(),
                "success": True
            }

            self.operation_history.append(operation_record)
            return operation_record

        except Exception as e:
            error_record = {
                "operation": operation,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "timestamp": start_time.isoformat(),
                "success": False
            }

            self.operation_history.append(error_record)
            return error_record

    async def _reverse_causality(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """因果律反転"""
        link_id = params.get("link_id")

        if link_id not in self.causal_graph.links:
            raise ValueError(f"Link {link_id} not found")

        link = self.causal_graph.links[link_id]

        # 因果関係を反転
        original_direction = link.direction
        link.direction = CausalDirection.BACKWARD if original_direction == CausalDirection.FORWARD else CausalDirection.FORWARD

        return {
            "link_id": link_id,
            "original_direction": original_direction.value,
            "new_direction": link.direction.value,
            "causality_impact": 0.7,
            "timeline_alteration": 0.3
        }

    async def _amplify_causality(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """因果律増幅"""
        link_id = params.get("link_id")
        amplification_factor = params.get("factor", 2.0)

        if link_id not in self.causal_graph.links:
            raise ValueError(f"Link {link_id} not found")

        link = self.causal_graph.links[link_id]
        original_strength = link.strength

        link.strength = min(1.0, link.strength * amplification_factor)

        return {
            "link_id": link_id,
            "original_strength": original_strength,
            "new_strength": link.strength,
            "amplification_factor": amplification_factor,
            "energy_required": (link.strength - original_strength) * 100
        }

    async def _create_quantum_entanglement(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """量子もつれ生成"""
        event1_id = params.get("event1_id")
        event2_id = params.get("event2_id")

        entanglement_id = await self.quantum_engine.entangle_events(event1_id, event2_id)

        return {
            "entanglement_id": entanglement_id,
            "event1_id": event1_id,
            "event2_id": event2_id,
            "quantum_correlation": 0.95,
            "instantaneous_action": True
        }

    async def _temporal_isolation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """時間的分離"""
        event_id = params.get("event_id")
        isolation_duration = params.get("duration", 60.0)

        lock_id = await self.temporal_controller.create_temporal_lock(event_id, isolation_duration)

        return {
            "lock_id": lock_id,
            "event_id": event_id,
            "isolation_duration": isolation_duration,
            "temporal_protection": 0.9
        }

    async def _causality_dampening(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """因果律減衰"""
        event_id = params.get("event_id")
        dampening_factor = params.get("factor", 0.5)

        # イベントに関連する全リンクの強度を減衰
        affected_links = []
        for link_id, link in self.causal_graph.links.items():
            if link.cause_event_id == event_id or link.effect_event_id == event_id:
                original_strength = link.strength
                link.strength *= dampening_factor
                affected_links.append({
                    "link_id": link_id,
                    "original_strength": original_strength,
                    "new_strength": link.strength
                })

        return {
            "event_id": event_id,
            "dampening_factor": dampening_factor,
            "affected_links": len(affected_links),
            "link_details": affected_links
        }

    async def analyze_causality_network(self) -> Dict[str, Any]:
        """因果律ネットワーク分析"""
        # パラドックス検出
        paradox_analysis = await self.temporal_controller.detect_temporal_paradox(self.causal_graph)

        # ネットワーク統計
        network_stats = {
            "total_nodes": self.causal_graph.graph.number_of_nodes(),
            "total_edges": self.causal_graph.graph.number_of_edges(),
        }

        # 簡易統計
        total_nodes = network_stats["total_nodes"]
        total_edges = network_stats["total_edges"]
        max_edges = total_nodes * (total_nodes - 1) if total_nodes > 1 else 1
        network_stats.update({
            "density": total_edges / max_edges if max_edges > 0 else 0,
            "strongly_connected_components": 1,  # 簡易推定
            "weakly_connected_components": 1
        })

        # 量子状態統計
        quantum_stats = {
            "quantum_events": len(self.quantum_engine.quantum_states),
            "entanglement_pairs": len(self.quantum_engine.entanglement_pairs),
            "measurements_performed": len(self.quantum_engine.measurement_history)
        }

        return {
            "network_analysis": network_stats,
            "quantum_analysis": quantum_stats,
            "paradox_analysis": paradox_analysis,
            "system_stats": self.system_stats,
            "timeline_integrity": paradox_analysis.get("timeline_stability", 1.0)
        }

# デモ実行
async def causality_demo():
    """因果律制御システムデモ"""
    print("🔮 Causality Control System Demo")
    print("=" * 60)

    system = CausalityControlSystem()

    # 1. 基本因果イベント作成
    print("\n📍 Creating causal events...")

    cause_id = await system.create_causal_event({
        "description": "User clicks button",
        "location": "web_interface",
        "energy": 1.0
    }, EventType.CAUSE)

    effect_id = await system.create_causal_event({
        "description": "System processes request",
        "location": "backend_server",
        "energy": 5.0
    }, EventType.EFFECT)

    quantum_id = await system.create_causal_event({
        "description": "Quantum computation",
        "location": "quantum_processor",
        "energy": 50.0
    }, EventType.QUANTUM_STATE)

    print(f"Created events: {cause_id}, {effect_id}, {quantum_id}")

    # 2. 因果関係確立
    print("\n🔗 Establishing causality...")

    link1 = await system.establish_causality(cause_id, effect_id, CausalityType.DETERMINISTIC, 0.9)
    link2 = await system.establish_causality(effect_id, quantum_id, CausalityType.QUANTUM, 0.7)

    print(f"Created causal links: {link1}, {link2}")

    # 3. 因果律操作テスト
    print("\n⚡ Testing causality manipulations...")

    # 因果律増幅
    amplify_op = {
        "type": "amplify_causality",
        "parameters": {
            "link_id": link1,
            "factor": 1.5
        }
    }

    amplify_result = await system.manipulate_causality(amplify_op)
    print(f"Causality amplification: {amplify_result['result']['new_strength']:.3f}")

    # 量子もつれ生成
    entangle_op = {
        "type": "create_quantum_entanglement",
        "parameters": {
            "event1_id": cause_id,
            "event2_id": quantum_id
        }
    }

    entangle_result = await system.manipulate_causality(entangle_op)
    print(f"Quantum entanglement created: {entangle_result['result']['entanglement_id']}")

    # 時間的分離
    isolation_op = {
        "type": "temporal_isolation",
        "parameters": {
            "event_id": effect_id,
            "duration": 10.0
        }
    }

    isolation_result = await system.manipulate_causality(isolation_op)
    print(f"Temporal isolation: {isolation_result['result']['lock_id']}")

    # 4. 量子測定
    print("\n🔬 Performing quantum measurement...")

    measurement = await system.quantum_engine.measure_quantum_causality(quantum_id)
    print(f"Measurement result: {measurement['measurement_result']}")
    print(f"Causality impact: {measurement['causality_impact']:.3f}")

    # 5. 因果律ネットワーク分析
    print("\n📊 Analyzing causality network...")

    analysis = await system.analyze_causality_network()

    print("Network Statistics:")
    print(f"  Nodes: {analysis['network_analysis']['total_nodes']}")
    print(f"  Edges: {analysis['network_analysis']['total_edges']}")
    print(f"  Density: {analysis['network_analysis']['density']:.3f}")

    print("Quantum Statistics:")
    print(f"  Quantum events: {analysis['quantum_analysis']['quantum_events']}")
    print(f"  Entanglement pairs: {analysis['quantum_analysis']['entanglement_pairs']}")
    print(f"  Measurements: {analysis['quantum_analysis']['measurements_performed']}")

    print("Paradox Analysis:")
    print(f"  Paradoxes detected: {analysis['paradox_analysis']['paradoxes_detected']}")
    print(f"  Timeline stability: {analysis['paradox_analysis']['timeline_stability']:.3f}")
    print(f"  Timeline integrity: {analysis['timeline_integrity']:.3f}")

    # 6. システム統計
    print("\n📈 System Statistics:")
    print(f"Total operations performed: {len(system.operation_history)}")
    print(f"Success rate: {sum(1 for op in system.operation_history if op['success']) / len(system.operation_history) * 100:.1f}%")

if __name__ == "__main__":
    asyncio.run(causality_demo())
