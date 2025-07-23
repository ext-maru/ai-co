#!/usr/bin/env python3
"""
📊 Analysis Magic Package - 分析魔法パッケージ
============================================

Ancient Elderの8つの古代魔法の一つ。
データ分析、トレンド検出、相関分析、洞察生成を担当する分析魔法の実装。

OSS First原則に基づく高性能データ分析ライブラリ:
- NumPy: 数値計算とベクトル演算
- Pandas: データ操作と分析
- SciPy: 統計分析と科学計算
- Scikit-learn: 機械学習とデータマイニング
- Statsmodels: 統計モデリングと時系列分析
- NetworkX: ネットワーク分析

Author: Claude Elder
Created: 2025-07-23
Version: 1.0.0
"""

from .analysis_magic import AnalysisMagic

# パッケージメタデータ
__version__ = "1.0.0"
__author__ = "Claude Elder"
__email__ = "noreply@anthropic.com"
__description__ = "Advanced data analysis magic for Ancient Elder system"

# 公開API
__all__ = [
    "AnalysisMagic",
]

# 魔法能力の説明
MAGIC_CAPABILITIES = {
    "DATA_ANALYSIS": "記述統計・推定統計・仮説検定による包括的データ分析",
    "TREND_DETECTION": "時系列トレンド・パターン・変化点の自動検出",
    "CORRELATION_ANALYSIS": "単変量・多変量・因果関係の高度な相関分析",
    "INSIGHT_GENERATION": "自動洞察生成・異常検出・特徴重要度分析"
}

# サポートする分析手法
SUPPORTED_METHODS = {
    "descriptive_statistics": [
        "mean", "median", "mode", "std", "variance", 
        "skewness", "kurtosis", "quartiles", "confidence_intervals"
    ],
    "correlation_methods": [
        "pearson", "spearman", "kendall", "partial_correlation", 
        "lag_correlation", "causality_analysis"
    ],
    "trend_analysis": [
        "linear_trend", "polynomial_trend", "seasonal_decomposition",
        "change_point_detection", "pattern_recognition"
    ],
    "multivariate_analysis": [
        "pca", "factor_analysis", "clustering", "dimensionality_reduction"
    ],
    "anomaly_detection": [
        "z_score", "iqr", "isolation_forest", "statistical_outliers"
    ],
    "feature_analysis": [
        "feature_importance", "mutual_information", "correlation_ranking"
    ],
    "quality_assessment": [
        "completeness", "consistency", "accuracy", "validity"
    ]
}

# OSS依存関係情報
OSS_DEPENDENCIES = {
    "numpy": {
        "purpose": "高性能数値計算・配列操作",
        "features": ["ベクトル演算", "統計関数", "線形代数"],
        "performance": "C/Fortran最適化による高速処理"
    },
    "pandas": {
        "purpose": "データ操作・分析・変換",
        "features": ["DataFrame操作", "時系列処理", "データクリーニング"],
        "performance": "メモリ効率的なデータ構造"
    },
    "scipy": {
        "purpose": "科学計算・統計分析", 
        "features": ["仮説検定", "確率分布", "最適化"],
        "performance": "数値計算ライブラリの最適化"
    },
    "scikit-learn": {
        "purpose": "機械学習・データマイニング",
        "features": ["クラスタリング", "次元削減", "特徴選択"],
        "performance": "並列処理対応の効率的アルゴリズム"
    },
    "statsmodels": {
        "purpose": "統計モデリング・時系列分析",
        "features": ["回帰分析", "時系列分解", "因果関係検定"],
        "performance": "統計的推論に特化した実装"
    },
    "networkx": {
        "purpose": "ネットワーク分析・グラフ理論",
        "features": ["中心性分析", "コミュニティ検出", "グラフ可視化"],
        "performance": "大規模ネットワーク対応アルゴリズム"
    }
}

# バージョン互換性情報
COMPATIBILITY_INFO = {
    "python_version": ">=3.8",
    "numpy_version": ">=1.21.0",
    "pandas_version": ">=1.3.0", 
    "scipy_version": ">=1.7.0",
    "scikit_learn_version": ">=1.0.0",
    "statsmodels_version": ">=0.12.0",
    "networkx_version": ">=2.6.0"
}

# パフォーマンス仕様
PERFORMANCE_SPECS = {
    "max_data_points": 100000,
    "max_features": 1000,
    "memory_efficient": True,
    "parallel_processing": True,
    "caching_enabled": True,
    "typical_response_time_ms": {
        "descriptive_stats": "<100ms",
        "correlation_analysis": "<500ms", 
        "multivariate_analysis": "<2000ms",
        "comprehensive_analysis": "<5000ms"
    }
}

# 使用例
USAGE_EXAMPLES = {
    "basic_analysis": """
# 基本的な記述統計分析
magic = AnalysisMagic()
result = await magic.cast_magic("descriptive_analysis", {
    "data": dataframe,
    "include_distribution": True,
    "confidence_level": 0.95
})
""",
    "correlation_analysis": """
# 相関分析の実行
result = await magic.cast_magic("correlation_analysis", {
    "data": dataframe,
    "method": "pearson",
    "include_pvalues": True
})
""",
    "trend_detection": """
# トレンド検出
result = await magic.cast_magic("trend_analysis", {
    "data": {"timestamps": dates, "values": values},
    "trend_methods": ["linear", "seasonal"],
    "decomposition": True
})
""",
    "insight_generation": """
# 自動洞察生成
result = await magic.cast_magic("insight_generation", {
    "data": dataframe,
    "insight_types": ["statistical", "correlation", "outlier"],
    "confidence_threshold": 0.8
})
"""
}

def get_magic_info():
    """Analysis Magic の詳細情報を取得"""
    return {
        "name": "Analysis Magic",
        "version": __version__,
        "description": __description__,
        "capabilities": MAGIC_CAPABILITIES,
        "supported_methods": SUPPORTED_METHODS,
        "oss_dependencies": OSS_DEPENDENCIES,
        "performance_specs": PERFORMANCE_SPECS,
        "compatibility": COMPATIBILITY_INFO,
        "usage_examples": USAGE_EXAMPLES
    }

def validate_dependencies():
    """OSS依存関係の検証"""
    try:
        import numpy as np
        versions = {"numpy": np.__version__}
        
        try:
            import pandas as pd
            versions["pandas"] = pd.__version__
        except ImportError:
            pass
            
        try:
            import scipy
            versions["scipy"] = scipy.__version__
        except ImportError:
            pass
            
        try:
            import sklearn
            versions["scikit-learn"] = sklearn.__version__
        except ImportError:
            pass
            
        try:
            import statsmodels
            versions["statsmodels"] = statsmodels.__version__
        except ImportError:
            pass
            
        try:
            import networkx as nx
            versions["networkx"] = nx.__version__
        except ImportError:
            pass
        
        return {
            "status": "success",
            "message": "Dependencies validated",
            "versions": versions
        }
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Critical dependency missing: {str(e)}",
            "recommendation": "Install numpy at minimum: pip install numpy pandas scipy scikit-learn statsmodels networkx"
        }

# パッケージ初期化時の依存関係チェック
_dependency_check = validate_dependencies()
if _dependency_check["status"] == "error":
    import warnings
    warnings.warn(
        f"Analysis Magic dependency check failed: {_dependency_check['message']}. "
        f"{_dependency_check.get('recommendation', '')}",
        UserWarning
    )