#!/usr/bin/env python3
"""
Self-Evolving Code Generator
自己進化コードジェネレーター

🧬 nWo Global Domination Framework - Evolutionary Code Engine
Think it, Rule it, Own it - 進化的コード生成システム
"""

import asyncio
import json
import time
import logging
import ast
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import hashlib
import inspect
import textwrap
import re
from collections import defaultdict, deque
import threading
import queue
import concurrent.futures


class EvolutionStrategy(Enum):
    """進化戦略"""
    GENETIC_ALGORITHM = "genetic_algorithm"
    SIMULATED_ANNEALING = "simulated_annealing"
    PARTICLE_SWARM = "particle_swarm"
    NEURAL_EVOLUTION = "neural_evolution"
    HYBRID_EVOLUTION = "hybrid_evolution"


class MutationType(Enum):
    """突然変異タイプ"""
    VARIABLE_RENAME = "variable_rename"
    EXPRESSION_MODIFY = "expression_modify"
    STRUCTURE_CHANGE = "structure_change"
    ALGORITHM_REPLACE = "algorithm_replace"
    OPTIMIZATION_INSERT = "optimization_insert"
    PERFORMANCE_TUNE = "performance_tune"
    LOGIC_ENHANCE = "logic_enhance"


class FitnessMetric(Enum):
    """適応度メトリック"""
    PERFORMANCE = "performance"
    READABILITY = "readability"
    MAINTAINABILITY = "maintainability"
    MEMORY_EFFICIENCY = "memory_efficiency"
    CPU_EFFICIENCY = "cpu_efficiency"
    CODE_COMPLEXITY = "code_complexity"
    TEST_COVERAGE = "test_coverage"


@dataclass
class CodeGene:
    """コード遺伝子"""
    gene_id: str
    code_snippet: str
    function_name: str
    gene_type: str
    fitness_scores: Dict[str, float]
    generation: int
    parent_genes: List[str]
    mutation_history: List[str]
    performance_metrics: Dict[str, Any]
    created_at: str


@dataclass
class EvolutionResult:
    """進化結果"""
    result_id: str
    target_function: str
    evolved_code: str
    generations: int
    best_fitness: float
    fitness_history: List[float]
    optimization_metrics: Dict[str, float]
    evolution_time: float
    convergence_generation: int
    final_genes: List[CodeGene]


@dataclass
class PopulationStats:
    """個体群統計"""
    generation: int
    population_size: int
    average_fitness: float
    best_fitness: float
    worst_fitness: float
    diversity_score: float
    convergence_rate: float
    mutation_rate: float
    selection_pressure: float


class GeneticOperators:
    """遺伝的操作子"""

    def __init__(self):
        self.logger = self._setup_logger()

        # 突然変異操作マップ
        self.mutation_operators = {
            MutationType.VARIABLE_RENAME: self._mutate_variable_rename,
            MutationType.EXPRESSION_MODIFY: self._mutate_expression_modify,
            MutationType.STRUCTURE_CHANGE: self._mutate_structure_change,
            MutationType.ALGORITHM_REPLACE: self._mutate_algorithm_replace,
            MutationType.OPTIMIZATION_INSERT: self._mutate_optimization_insert,
            MutationType.PERFORMANCE_TUNE: self._mutate_performance_tune,
            MutationType.LOGIC_ENHANCE: self._mutate_logic_enhance
        }

        # 交叉操作
        self.crossover_operators = [
            self._uniform_crossover,
            self._single_point_crossover,
            self._semantic_crossover,
            self._block_crossover
        ]

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("genetic_operators")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Genetic Ops - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def mutate_gene(self, gene: CodeGene, mutation_type: MutationType,
                   mutation_rate: float = 0.1) -> CodeGene:
        """遺伝子突然変異"""
        if random.random() > mutation_rate:
            return gene

        mutation_func = self.mutation_operators.get(mutation_type)
        if not mutation_func:
            return gene

        try:
            mutated_code = mutation_func(gene.code_snippet)

            # 新しい遺伝子作成
            new_gene = CodeGene(
                gene_id=f"mutated_{gene.gene_id}_{int(time.time())}",
                code_snippet=mutated_code,
                function_name=gene.function_name,
                gene_type=gene.gene_type,
                fitness_scores={},
                generation=gene.generation + 1,
                parent_genes=[gene.gene_id],
                mutation_history=gene.mutation_history + [mutation_type.value],
                performance_metrics={},
                created_at=datetime.now().isoformat()
            )

            self.logger.info(f"🧬 Mutated gene: {mutation_type.value}")
            return new_gene

        except Exception as e:
            self.logger.warning(f"Mutation failed: {e}")
            return gene

    def _mutate_variable_rename(self, code: str) -> str:
        """変数名変更突然変異"""
        # 簡単な変数名変更
        variable_patterns = [
            (r'\btemp\b', 'temporary'),
            (r'\bval\b', 'value'),
            (r'\bres\b', 'result'),
            (r'\bi\b', 'index'),
            (r'\bj\b', 'idx'),
            (r'\bx\b', 'data'),
            (r'\by\b', 'output')
        ]

        pattern, replacement = random.choice(variable_patterns)
        return re.sub(pattern, replacement, code)

    def _mutate_expression_modify(self, code: str) -> str:
        """式変更突然変異"""
        # 演算子変更
        operator_mutations = [
            (r'\+', '-'),
            (r'-', '+'),
            (r'\*', '//'),
            (r'//', '*'),
            (r'==', '!='),
            (r'!=', '=='),
            (r'<=', '<'),
            (r'>=', '>')
        ]

        if operator_mutations:
            pattern, replacement = random.choice(operator_mutations)
            # 安全な置換のため、確率的に適用
            if random.random() < 0.3:
                return re.sub(pattern, replacement, code, count=1)

        return code

    def _mutate_structure_change(self, code: str) -> str:
        """構造変更突然変異"""
        # ループ構造の変更など
        if 'for ' in code and random.random() < 0.2:
            # for文をリスト内包表記に変更（可能な場合）
            if 'append' in code:
                return self._convert_for_to_comprehension(code)

        return code

    def _convert_for_to_comprehension(self, code: str) -> str:
        """for文をリスト内包表記に変換"""
        # 簡単なfor文の変換例
        lines = code.split('\n')
        result_lines = []

        for line in lines:
            if 'for ' in line and 'in ' in line:
                # 簡単なパターンマッチング
                result_lines.append(line + "  # Converted pattern")
            else:
                result_lines.append(line)

        return '\n'.join(result_lines)

    def _mutate_algorithm_replace(self, code: str) -> str:
        """アルゴリズム置換突然変異"""
        # ソートアルゴリズムの置換
        if 'sort(' in code:
            return code.replace('sort()', 'sorted(key=lambda x: x)')

        # 検索アルゴリズムの変更
        if 'linear_search' in code:
            return code.replace('linear_search', 'binary_search')

        return code

    def _mutate_optimization_insert(self, code: str) -> str:
        """最適化挿入突然変異"""
        # キャッシュの追加
        if 'def ' in code and '@' not in code:
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    lines.insert(i, '@lru_cache(maxsize=128)')
                    break
            return '\n'.join(lines)

        return code

    def _mutate_performance_tune(self, code: str) -> str:
        """性能調整突然変異"""
        # NumPy最適化の追加
        if 'import ' in code and 'numpy' not in code:
            if random.random() < 0.3:
                return 'import numpy as np\n' + code

        # リスト操作の最適化
        if '.append(' in code:
            return code.replace('.append(', '.extend([') + '])'

        return code

    def _mutate_logic_enhance(self, code: str) -> str:
        """ロジック強化突然変異"""
        # エラー処理の追加
        if 'try:' not in code and 'def ' in code:
            lines = code.split('\n')
            result_lines = []
            in_function = False

            for line in lines:
                if line.strip().startswith('def '):
                    in_function = True
                    result_lines.append(line)
                elif in_function and line.strip() and not line.startswith(' '):
                    in_function = False
                    result_lines.append(line)
                elif in_function and line.strip():
                    # 関数内にtry-catch追加
                    if 'return ' in line:
                        indent = len(line) - len(line.lstrip())
                        result_lines.append(' ' * indent + 'try:')
                        result_lines.append(' ' * (indent + 4) + line.strip())
                        result_lines.append(' ' * indent + 'except Exception as e:')
                        result_lines.append(' ' * (indent + 4) + 'return None')
                    else:
                        result_lines.append(line)
                else:
                    result_lines.append(line)

            return '\n'.join(result_lines)

        return code

    def crossover_genes(self, parent1: CodeGene, parent2: CodeGene) -> Tuple[CodeGene, CodeGene]:
        """遺伝子交叉"""
        crossover_func = random.choice(self.crossover_operators)

        try:
            child1_code, child2_code = crossover_func(parent1.code_snippet, parent2.code_snippet)

            # 子遺伝子作成
            child1 = CodeGene(
                gene_id=f"cross_{parent1.gene_id}_{parent2.gene_id}_{int(time.time())}_1",
                code_snippet=child1_code,
                function_name=parent1.function_name,
                gene_type=parent1.gene_type,
                fitness_scores={},
                generation=max(parent1.generation, parent2.generation) + 1,
                parent_genes=[parent1.gene_id, parent2.gene_id],
                mutation_history=[],
                performance_metrics={},
                created_at=datetime.now().isoformat()
            )

            child2 = CodeGene(
                gene_id=f"cross_{parent1.gene_id}_{parent2.gene_id}_{int(time.time())}_2",
                code_snippet=child2_code,
                function_name=parent2.function_name,
                gene_type=parent2.gene_type,
                fitness_scores={},
                generation=max(parent1.generation, parent2.generation) + 1,
                parent_genes=[parent1.gene_id, parent2.gene_id],
                mutation_history=[],
                performance_metrics={},
                created_at=datetime.now().isoformat()
            )

            self.logger.info("🧬 Genes crossed successfully")
            return child1, child2

        except Exception as e:
            self.logger.warning(f"Crossover failed: {e}")
            return parent1, parent2

    def _uniform_crossover(self, code1: str, code2: str) -> Tuple[str, str]:
        """一様交叉"""
        lines1 = code1.split('\n')
        lines2 = code2.split('\n')

        max_len = max(len(lines1), len(lines2))

        child1_lines = []
        child2_lines = []

        for i in range(max_len):
            if random.random() < 0.5:
                child1_lines.append(lines1[i] if i < len(lines1) else "")
                child2_lines.append(lines2[i] if i < len(lines2) else "")
            else:
                child1_lines.append(lines2[i] if i < len(lines2) else "")
                child2_lines.append(lines1[i] if i < len(lines1) else "")

        return '\n'.join(child1_lines), '\n'.join(child2_lines)

    def _single_point_crossover(self, code1: str, code2: str) -> Tuple[str, str]:
        """一点交叉"""
        lines1 = code1.split('\n')
        lines2 = code2.split('\n')

        min_len = min(len(lines1), len(lines2))
        if min_len <= 1:
            return code1, code2

        crossover_point = random.randint(1, min_len - 1)

        child1 = '\n'.join(lines1[:crossover_point] + lines2[crossover_point:])
        child2 = '\n'.join(lines2[:crossover_point] + lines1[crossover_point:])

        return child1, child2

    def _semantic_crossover(self, code1: str, code2: str) -> Tuple[str, str]:
        """意味的交叉"""
        # 関数定義を保持しながら交叉
        def_pattern = r'def\s+\w+\([^)]*\):'

        defs1 = re.findall(def_pattern, code1)
        defs2 = re.findall(def_pattern, code2)

        if defs1 and defs2:
            # 関数定義を交換
            child1 = re.sub(def_pattern, defs2[0] if defs2 else defs1[0], code1, count=1)
            child2 = re.sub(def_pattern, defs1[0] if defs1 else defs2[0], code2, count=1)
            return child1, child2

        return self._uniform_crossover(code1, code2)

    def _block_crossover(self, code1: str, code2: str) -> Tuple[str, str]:
        """ブロック交叉"""
        # インデントブロック単位での交叉
        blocks1 = self._extract_blocks(code1)
        blocks2 = self._extract_blocks(code2)

        if len(blocks1) > 1 and len(blocks2) > 1:
            # ランダムにブロックを交換
            idx1 = random.randint(0, len(blocks1) - 1)
            idx2 = random.randint(0, len(blocks2) - 1)

            new_blocks1 = blocks1.copy()
            new_blocks2 = blocks2.copy()

            new_blocks1[idx1], new_blocks2[idx2] = new_blocks2[idx2], new_blocks1[idx1]

            return '\n'.join(new_blocks1), '\n'.join(new_blocks2)

        return code1, code2

    def _extract_blocks(self, code: str) -> List[str]:
        """コードブロック抽出"""
        lines = code.split('\n')
        blocks = []
        current_block = []
        current_indent = 0

        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                if indent <= current_indent and current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = [line]
                    current_indent = indent
                else:
                    current_block.append(line)
                    if not current_block:
                        current_indent = indent
            else:
                current_block.append(line)

        if current_block:
            blocks.append('\n'.join(current_block))

        return blocks


class FitnessEvaluator:
    """適応度評価器"""

    def __init__(self):
        self.logger = self._setup_logger()

        # メトリック重み
        self.metric_weights = {
            FitnessMetric.PERFORMANCE: 0.25,
            FitnessMetric.READABILITY: 0.15,
            FitnessMetric.MAINTAINABILITY: 0.15,
            FitnessMetric.MEMORY_EFFICIENCY: 0.15,
            FitnessMetric.CPU_EFFICIENCY: 0.15,
            FitnessMetric.CODE_COMPLEXITY: 0.10,
            FitnessMetric.TEST_COVERAGE: 0.05
        }

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("fitness_evaluator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Fitness Eval - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def evaluate_fitness(self, gene: CodeGene) -> float:
        """適応度評価"""
        try:
            # 各メトリックを評価
            scores = {}

            scores[FitnessMetric.PERFORMANCE] = await self._evaluate_performance(gene)
            scores[FitnessMetric.READABILITY] = self._evaluate_readability(gene)
            scores[FitnessMetric.MAINTAINABILITY] = self._evaluate_maintainability(gene)
            scores[FitnessMetric.MEMORY_EFFICIENCY] = self._evaluate_memory_efficiency(gene)
            scores[FitnessMetric.CPU_EFFICIENCY] = self._evaluate_cpu_efficiency(gene)
            scores[FitnessMetric.CODE_COMPLEXITY] = self._evaluate_complexity(gene)
            scores[FitnessMetric.TEST_COVERAGE] = self._evaluate_test_coverage(gene)

            # 重み付き合計
            total_fitness = sum(
                scores[metric] * self.metric_weights[metric]
                for metric in scores
            )

            # スコアを遺伝子に保存
            gene.fitness_scores = {metric.value: score for metric, score in scores.items()}

            self.logger.info(f"📊 Fitness evaluated: {total_fitness:.3f}")
            return total_fitness

        except Exception as e:
            self.logger.error(f"Fitness evaluation error: {e}")
            return 0.0

    async def _evaluate_performance(self, gene: CodeGene) -> float:
        """性能評価"""
        try:
            # 簡単な実行時間測定
            start_time = time.time()

            # コード実行の模擬
            lines = len(gene.code_snippet.split('\n'))
            complexity_estimate = lines * 0.001  # 行数ベースの複雑度

            # 模擬実行時間
            await asyncio.sleep(complexity_estimate)

            execution_time = time.time() - start_time

            # 実行時間が短いほど高スコア
            performance_score = max(0.0, 1.0 - execution_time * 10)

            return performance_score

        except Exception:
            return 0.5  # デフォルト値

    def _evaluate_readability(self, gene: CodeGene) -> float:
        """可読性評価"""
        code = gene.code_snippet

        readability_score = 0.5  # ベーススコア

        # コメントの存在
        if '#' in code:
            readability_score += 0.1

        # 適切な変数名
        if any(name in code for name in ['result', 'data', 'value', 'output']):
            readability_score += 0.1

        # 短すぎる変数名のペナルティ
        if re.search(r'\b[a-z]\b', code):
            readability_score -= 0.1

        # 行の長さ
        lines = code.split('\n')
        long_lines = sum(1 for line in lines if len(line) > 80)
        if long_lines == 0:
            readability_score += 0.1

        # 適切なインデント
        if all(line.startswith('    ') or not line.strip() or not line.startswith(' ')
               for line in lines):
            readability_score += 0.1

        return max(0.0, min(1.0, readability_score))

    def _evaluate_maintainability(self, gene: CodeGene) -> float:
        """保守性評価"""
        code = gene.code_snippet

        maintainability_score = 0.5

        # 関数サイズ
        lines = [line for line in code.split('\n') if line.strip()]
        if len(lines) <= 20:
            maintainability_score += 0.2
        elif len(lines) > 50:
            maintainability_score -= 0.2

        # 複雑性（ネストレベル）
        max_indent = 0
        for line in code.split('\n'):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)

        if max_indent <= 8:  # 2レベルまで
            maintainability_score += 0.15
        elif max_indent > 16:  # 4レベル以上
            maintainability_score -= 0.15

        # エラー処理の存在
        if 'try:' in code and 'except' in code:
            maintainability_score += 0.1

        # ドキュメント文字列
        if '"""' in code or "'''" in code:
            maintainability_score += 0.1

        return max(0.0, min(1.0, maintainability_score))

    def _evaluate_memory_efficiency(self, gene: CodeGene) -> float:
        """メモリ効率評価"""
        code = gene.code_snippet

        memory_score = 0.7  # ベーススコア

        # リスト内包表記の使用
        if '[' in code and 'for' in code and 'in' in code:
            memory_score += 0.1

        # 不要な変数の回避
        temp_vars = len(re.findall(r'\btemp\b|\btmp\b', code))
        memory_score -= temp_vars * 0.05

        # ジェネレータの使用
        if 'yield' in code:
            memory_score += 0.15

        # 大きなリスト操作のペナルティ
        if 'range(' in code:
            range_matches = re.findall(r'range\((\d+)', code)
            for match in range_matches:
                if int(match) > 10000:
                    memory_score -= 0.1

        return max(0.0, min(1.0, memory_score))

    def _evaluate_cpu_efficiency(self, gene: CodeGene) -> float:
        """CPU効率評価"""
        code = gene.code_snippet

        cpu_score = 0.6

        # 効率的なアルゴリズム
        if 'sorted(' in code:
            cpu_score += 0.1
        if 'set(' in code:
            cpu_score += 0.1
        if 'dict(' in code:
            cpu_score += 0.05

        # 非効率なパターンのペナルティ
        if 'in' in code and 'list' in code:
            cpu_score -= 0.1  # リストでのin検索

        # ネストループのペナルティ
        nested_loops = len(re.findall(r'for.*in.*:.*for.*in.*:', code, re.DOTALL))
        cpu_score -= nested_loops * 0.15

        # キャッシュの使用
        if '@lru_cache' in code or '@cache' in code:
            cpu_score += 0.2

        return max(0.0, min(1.0, cpu_score))

    def _evaluate_complexity(self, gene: CodeGene) -> float:
        """複雑度評価（低いほど良い）"""
        code = gene.code_snippet

        # サイクロマティック複雑度の簡易版
        complexity_indicators = [
            'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'and', 'or'
        ]

        complexity = sum(code.count(indicator) for indicator in complexity_indicators)

        # 複雑度が低いほど高スコア
        complexity_score = max(0.0, 1.0 - complexity * 0.1)

        return complexity_score

    def _evaluate_test_coverage(self, gene: CodeGene) -> float:
        """テストカバレッジ評価"""
        code = gene.code_snippet

        # 簡易的なテストカバレッジ評価
        test_score = 0.3

        # アサーションの存在
        if 'assert' in code:
            test_score += 0.3

        # テスト関数の存在
        if 'test_' in code or 'def test' in code:
            test_score += 0.4

        return min(1.0, test_score)


class SelfEvolvingCodeGenerator:
    """自己進化コードジェネレーター"""

    def __init__(self, population_size: int = 50, max_generations: int = 100):
        self.population_size = population_size
        self.max_generations = max_generations

        self.genetic_ops = GeneticOperators()
        self.fitness_evaluator = FitnessEvaluator()
        self.logger = self._setup_logger()

        # 進化パラメータ
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
        self.elite_ratio = 0.1
        self.selection_pressure = 2.0

        # 進化履歴
        self.evolution_history: List[EvolutionResult] = []
        self.population_stats: List[PopulationStats] = []

        # 並列処理
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

        self.logger.info("🧬 Self-Evolving Code Generator initialized")

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("code_generator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - Code Generator - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def evolve_code(self, target_function: str, requirements: Dict[str, Any]) -> EvolutionResult:
        """
        コード進化実行

        Args:
            target_function: 目標関数名
            requirements: 要求事項

        Returns:
            EvolutionResult: 進化結果
        """
        self.logger.info(f"🧬 Starting code evolution for: {target_function}")

        start_time = time.time()

        # 初期個体群生成
        population = await self._generate_initial_population(target_function, requirements)

        # 進化ループ
        best_fitness_history = []
        convergence_generation = -1

        for generation in range(self.max_generations):
            self.logger.info(f"🧬 Generation {generation + 1}/{self.max_generations}")

            # 適応度評価
            await self._evaluate_population(population)

            # 統計計算
            stats = self._calculate_population_stats(population, generation)
            self.population_stats.append(stats)
            best_fitness_history.append(stats.best_fitness)

            # 収束判定
            if self._check_convergence(best_fitness_history):
                convergence_generation = generation
                break

            # 次世代生成
            population = await self._generate_next_generation(population)

            # 動的パラメータ調整
            self._adjust_evolution_parameters(generation, stats)

        # 最良個体選択
        best_gene = max(population, key=lambda g: sum(g.fitness_scores.values()) if g.fitness_scores else 0)

        evolution_time = time.time() - start_time

        result = EvolutionResult(
            result_id=f"evolution_{target_function}_{int(time.time())}",
            target_function=target_function,
            evolved_code=best_gene.code_snippet,
            generations=generation + 1,
            best_fitness=sum(best_gene.fitness_scores.values()) if best_gene.fitness_scores else 0,
            fitness_history=best_fitness_history,
            optimization_metrics=self._calculate_optimization_metrics(population),
            evolution_time=evolution_time,
            convergence_generation=convergence_generation,
            final_genes=population[:5]  # トップ5
        )

        self.evolution_history.append(result)

        self.logger.info(f"✅ Evolution completed: {result.best_fitness:.3f} fitness")

        return result

    async def _generate_initial_population(self, target_function: str,
                                         requirements: Dict[str, Any]) -> List[CodeGene]:
        """初期個体群生成"""
        population = []

        # ベースコードテンプレート
        base_templates = self._get_code_templates(target_function, requirements)

        for i in range(self.population_size):
            # テンプレートからランダム選択
            template = random.choice(base_templates)

            # 初期変異適用
            mutated_code = await self._apply_initial_mutations(template)

            gene = CodeGene(
                gene_id=f"gen0_{target_function}_{i}",
                code_snippet=mutated_code,
                function_name=target_function,
                gene_type="function",
                fitness_scores={},
                generation=0,
                parent_genes=[],
                mutation_history=[],
                performance_metrics={},
                created_at=datetime.now().isoformat()
            )

            population.append(gene)

        self.logger.info(f"🧬 Generated initial population: {len(population)} genes")
        return population

    def _get_code_templates(self, target_function: str, requirements: Dict[str, Any]) -> List[str]:
        """コードテンプレート取得"""
        templates = []

        # 基本テンプレート
        basic_template = f"""def {target_function}(data):
    \"\"\"Generated function for {target_function}\"\"\"
    result = []
    for item in data:
        processed = item * 2
        result.append(processed)
    return result"""

        templates.append(basic_template)

        # 最適化テンプレート
        optimized_template = f"""def {target_function}(data):
    \"\"\"Optimized function for {target_function}\"\"\"
    return [item * 2 for item in data]"""

        templates.append(optimized_template)

        # エラーハンドリングテンプレート
        robust_template = f"""def {target_function}(data):
    \"\"\"Robust function for {target_function}\"\"\"
    try:
        result = []
        for item in data:
            if item is not None:
                processed = item * 2
                result.append(processed)
        return result
    except Exception as e:
        return []"""

        templates.append(robust_template)

        # 高性能テンプレート
        performance_template = f"""import numpy as np

def {target_function}(data):
    \"\"\"High performance function for {target_function}\"\"\"
    try:
        return np.array(data) * 2
    except:
        return [item * 2 for item in data if item is not None]"""

        templates.append(performance_template)

        # 要求事項に基づくカスタマイズ
        if requirements.get("use_numpy", False):
            templates.append(performance_template)

        if requirements.get("error_handling", True):
            templates.append(robust_template)

        return templates

    async def _apply_initial_mutations(self, code: str) -> str:
        """初期変異適用"""
        mutation_types = list(MutationType)

        # ランダムに1-3個の変異を適用
        num_mutations = random.randint(1, 3)
        mutated_code = code

        for _ in range(num_mutations):
            mutation_type = random.choice(mutation_types)

            # 一時的な遺伝子作成
            temp_gene = CodeGene(
                gene_id="temp",
                code_snippet=mutated_code,
                function_name="temp",
                gene_type="temp",
                fitness_scores={},
                generation=0,
                parent_genes=[],
                mutation_history=[],
                performance_metrics={},
                created_at=""
            )

            mutated_gene = self.genetic_ops.mutate_gene(temp_gene, mutation_type, 0.5)
            mutated_code = mutated_gene.code_snippet

        return mutated_code

    async def _evaluate_population(self, population: List[CodeGene]):
        """個体群評価"""
        # 並列評価
        evaluation_tasks = [
            self.fitness_evaluator.evaluate_fitness(gene)
            for gene in population
        ]

        await asyncio.gather(*evaluation_tasks)

    def _calculate_population_stats(self, population: List[CodeGene], generation: int) -> PopulationStats:
        """個体群統計計算"""
        fitness_values = [
            sum(gene.fitness_scores.values()) if gene.fitness_scores else 0
            for gene in population
        ]

        if not fitness_values:
            fitness_values = [0.0]

        # 多様性スコア計算
        diversity_score = self._calculate_diversity(population)

        stats = PopulationStats(
            generation=generation,
            population_size=len(population),
            average_fitness=np.mean(fitness_values),
            best_fitness=max(fitness_values),
            worst_fitness=min(fitness_values),
            diversity_score=diversity_score,
            convergence_rate=self._calculate_convergence_rate(fitness_values),
            mutation_rate=self.mutation_rate,
            selection_pressure=self.selection_pressure
        )

        self.logger.info(f"📊 Gen {generation}: Best={stats.best_fitness:.3f}, Avg={stats.average_fitness:.3f}")

        return stats

    def _calculate_diversity(self, population: List[CodeGene]) -> float:
        """個体群多様性計算"""
        if len(population) < 2:
            return 0.0

        # コード類似度基づく多様性
        unique_codes = set(gene.code_snippet for gene in population)
        diversity = len(unique_codes) / len(population)

        return diversity

    def _calculate_convergence_rate(self, fitness_values: List[float]) -> float:
        """収束率計算"""
        if not fitness_values:
            return 0.0

        fitness_std = np.std(fitness_values)
        fitness_mean = np.mean(fitness_values)

        if fitness_mean == 0:
            return 0.0

        convergence_rate = 1.0 - (fitness_std / fitness_mean)
        return max(0.0, convergence_rate)

    def _check_convergence(self, fitness_history: List[float]) -> bool:
        """収束判定"""
        if len(fitness_history) < 10:
            return False

        # 最近10世代の改善がほとんどない場合
        recent_fitness = fitness_history[-10:]
        improvement = max(recent_fitness) - min(recent_fitness)

        return improvement < 0.001

    async def _generate_next_generation(self, population: List[CodeGene]) -> List[CodeGene]:
        """次世代生成"""
        # 適応度でソート
        sorted_population = sorted(
            population,
            key=lambda g: sum(g.fitness_scores.values()) if g.fitness_scores else 0,
            reverse=True
        )

        next_generation = []

        # エリート保存
        elite_count = int(self.population_size * self.elite_ratio)
        next_generation.extend(sorted_population[:elite_count])

        # 残りを交叉・突然変異で生成
        while len(next_generation) < self.population_size:
            # 親選択
            parent1 = self._tournament_selection(sorted_population)
            parent2 = self._tournament_selection(sorted_population)

            # 交叉
            if random.random() < self.crossover_rate:
                child1, child2 = self.genetic_ops.crossover_genes(parent1, parent2)
            else:
                child1, child2 = parent1, parent2

            # 突然変異
            mutation_type = random.choice(list(MutationType))
            child1 = self.genetic_ops.mutate_gene(child1, mutation_type, self.mutation_rate)
            child2 = self.genetic_ops.mutate_gene(child2, mutation_type, self.mutation_rate)

            next_generation.extend([child1, child2])

        # 個体数調整
        return next_generation[:self.population_size]

    def _tournament_selection(self, population: List[CodeGene]) -> CodeGene:
        """トーナメント選択"""
        tournament_size = int(len(population) * 0.1) + 1
        tournament = random.sample(population, min(tournament_size, len(population)))

        winner = max(
            tournament,
            key=lambda g: sum(g.fitness_scores.values()) if g.fitness_scores else 0
        )

        return winner

    def _adjust_evolution_parameters(self, generation: int, stats: PopulationStats):
        """進化パラメータ動的調整"""
        # 収束率に基づく突然変異率調整
        if stats.convergence_rate > 0.8:
            self.mutation_rate = min(0.3, self.mutation_rate * 1.1)
        elif stats.convergence_rate < 0.3:
            self.mutation_rate = max(0.05, self.mutation_rate * 0.9)

        # 多様性に基づく選択圧調整
        if stats.diversity_score < 0.3:
            self.selection_pressure = max(1.5, self.selection_pressure * 0.9)
        elif stats.diversity_score > 0.8:
            self.selection_pressure = min(3.0, self.selection_pressure * 1.1)

    def _calculate_optimization_metrics(self, population: List[CodeGene]) -> Dict[str, float]:
        """最適化メトリクス計算"""
        if not population:
            return {}

        fitness_values = [
            sum(gene.fitness_scores.values()) if gene.fitness_scores else 0
            for gene in population
        ]

        return {
            "final_average_fitness": np.mean(fitness_values),
            "fitness_variance": np.var(fitness_values),
            "population_diversity": self._calculate_diversity(population),
            "evolution_efficiency": max(fitness_values) / max(1.0, np.mean(fitness_values)),
            "convergence_stability": 1.0 - np.std(fitness_values[-10:]) if len(fitness_values) >= 10 else 0.0
        }

    async def evolve_multiple_functions(self, targets: List[Tuple[str, Dict[str, Any]]]) -> List[EvolutionResult]:
        """複数関数の並列進化"""
        self.logger.info(f"🧬 Starting parallel evolution for {len(targets)} functions")

        # 並列進化実行
        evolution_tasks = [
            self.evolve_code(target_func, requirements)
            for target_func, requirements in targets
        ]

        results = await asyncio.gather(*evolution_tasks)

        self.logger.info(f"✅ Parallel evolution completed: {len(results)} results")
        return results

    def get_evolution_summary(self) -> Dict[str, Any]:
        """進化サマリー取得"""
        if not self.evolution_history:
            return {"message": "No evolution history available"}

        return {
            "total_evolutions": len(self.evolution_history),
            "average_generations": np.mean([r.generations for r in self.evolution_history]),
            "average_fitness": np.mean([r.best_fitness for r in self.evolution_history]),
            "average_evolution_time": np.mean([r.evolution_time for r in self.evolution_history]),
            "successful_convergences": len([r for r in self.evolution_history if r.convergence_generation >= 0]),
            "best_overall_fitness": max([r.best_fitness for r in self.evolution_history]),
            "evolution_efficiency": len([r for r in self.evolution_history if r.evolution_time < 60]) / len(self.evolution_history)
        }

    def export_best_genes(self, output_dir: str = "evolved_code"):
        """最良遺伝子のエクスポート"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        for result in self.evolution_history:
            filename = f"{result.target_function}_evolved.py"
            filepath = output_path / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Evolved code for {result.target_function}\n")
                f.write(f"# Fitness: {result.best_fitness:.3f}\n")
                f.write(f"# Generations: {result.generations}\n")
                f.write(f"# Evolution time: {result.evolution_time:.2f}s\n\n")
                f.write(result.evolved_code)

        self.logger.info(f"📁 Exported {len(self.evolution_history)} evolved codes to {output_dir}")


# 使用例とデモ
async def demo_self_evolving_code_generator():
    """Self-Evolving Code Generatorのデモ"""
    print("🧬 Self-Evolving Code Generator Demo")
    print("=" * 60)

    generator = SelfEvolvingCodeGenerator(population_size=20, max_generations=10)

    # 単一関数進化
    print("\n🧬 Single Function Evolution:")
    target_function = "process_data"
    requirements = {
        "use_numpy": True,
        "error_handling": True,
        "optimize_performance": True
    }

    result = await generator.evolve_code(target_function, requirements)

    print(f"\n📊 Evolution Results:")
    print(f"   Target Function: {result.target_function}")
    print(f"   Generations: {result.generations}")
    print(f"   Best Fitness: {result.best_fitness:.3f}")
    print(f"   Evolution Time: {result.evolution_time:.2f}s")
    print(f"   Convergence Gen: {result.convergence_generation}")

    print(f"\n🧬 Evolved Code:")
    print("=" * 40)
    print(result.evolved_code)
    print("=" * 40)

    # 複数関数並列進化
    print(f"\n🧬 Parallel Multiple Function Evolution:")
    targets = [
        ("calculate_average", {"error_handling": True}),
        ("sort_data", {"optimize_performance": True}),
        ("validate_input", {"robust_validation": True})
    ]

    parallel_results = await generator.evolve_multiple_functions(targets)

    print(f"\n📊 Parallel Evolution Results:")
    for i, result in enumerate(parallel_results):
        print(f"   Function {i+1}: {result.target_function}")
        print(f"     Fitness: {result.best_fitness:.3f}")
        print(f"     Generations: {result.generations}")
        print(f"     Time: {result.evolution_time:.2f}s")

    # 進化サマリー
    print(f"\n📈 Evolution Summary:")
    summary = generator.get_evolution_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")

    # 遺伝子エクスポート
    generator.export_best_genes("demo_evolved_code")
    print(f"\n💾 Best genes exported to demo_evolved_code/")


if __name__ == "__main__":
    asyncio.run(demo_self_evolving_code_generator())
