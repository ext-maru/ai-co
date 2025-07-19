#!/usr/bin/env python3
"""
Day 1: pytest基礎実習 - エルダーズギルド研修
チーム教育プログラム Week 2

実習内容:
1. 基本テストの書き方
2. フィクスチャの使用
3. パラメータ化テスト
4. マークとテスト分類
"""

from typing import Dict, List

import pytest

# =============================================================================
# 実習1: 基本的なテスト
# =============================================================================


def add_elder_levels(level1: int, level2: int) -> int:
    """エルダーレベルの合計を計算"""
    return level1 + level2


def validate_elder_name(name: str) -> bool:
    """エルダー名の妥当性チェック"""
    if not name or len(name) < 2:
        return False
    return name.startswith("エルダー") or name.endswith("Elder")


# 基本テスト例
def test_add_elder_levels_basic():
    """基本的なアサーション例"""
    result = add_elder_levels(50, 30)
    assert result == 80


def test_validate_elder_name_valid():
    """有効なエルダー名のテスト"""
    assert validate_elder_name("エルダーmaru") == True
    assert validate_elder_name("Claude Elder") == True


def test_validate_elder_name_invalid():
    """無効なエルダー名のテスト"""
    assert validate_elder_name("") == False
    assert validate_elder_name("x") == False
    assert validate_elder_name("普通の人") == False


# =============================================================================
# 実習2: フィクスチャの使用
# =============================================================================


@pytest.fixture
def sample_elder_data():
    """テスト用エルダーデータ"""
    return {
        "name": "エルダーmaru",
        "level": 99,
        "skills": ["コード", "設計", "指導"],
        "guild": "エルダーズギルド",
    }


@pytest.fixture
def elder_list():
    """テスト用エルダーリスト"""
    return [
        {"name": "エルダーmaru", "role": "グランドエルダー"},
        {"name": "Claude Elder", "role": "開発実行責任者"},
        {"name": "ナレッジ賢者", "role": "知識管理"},
        {"name": "タスク賢者", "role": "進捗管理"},
    ]


def test_elder_data_structure(sample_elder_data):
    """フィクスチャを使用したテスト例"""
    assert sample_elder_data["name"] == "エルダーmaru"
    assert sample_elder_data["level"] == 99
    assert "コード" in sample_elder_data["skills"]
    assert len(sample_elder_data["skills"]) == 3


def test_elder_list_count(elder_list):
    """エルダーリストの検証"""
    assert len(elder_list) == 4
    assert elder_list[0]["role"] == "グランドエルダー"


# =============================================================================
# 実習3: パラメータ化テスト
# =============================================================================


@pytest.mark.parametrize(
    "level,expected_rank",
    [(1, "見習い"), (25, "一般"), (50, "上級"), (75, "達人"), (99, "エルダー")],
)
def test_elder_rank_calculation(level, expected_rank):
    """レベルに応じたランク判定テスト"""

    def get_elder_rank(level: int) -> str:
        if level < 10:
            return "見習い"
        elif level < 40:
            return "一般"
        elif level < 60:
            return "上級"
        elif level < 90:
            return "達人"
        else:
            return "エルダー"

    assert get_elder_rank(level) == expected_rank


@pytest.mark.parametrize(
    "name,valid",
    [
        ("エルダーmaru", True),
        ("Claude Elder", True),
        ("ナレッジ賢者", False),  # "賢者"で終わるが"Elder"ではない
        ("", False),
        ("普通の人", False),
    ],
)
def test_elder_name_validation_parametrized(name, valid):
    """パラメータ化された名前検証テスト"""
    assert validate_elder_name(name) == valid


# =============================================================================
# 実習4: マークとテスト分類
# =============================================================================


@pytest.mark.unit
def test_basic_calculation():
    """ユニットテスト例"""
    assert 2 + 2 == 4


@pytest.mark.integration
def test_elder_data_integration(sample_elder_data, elder_list):
    """統合テスト例 - 複数フィクスチャ使用"""
    # sample_elder_dataがelder_listに含まれているかチェック
    names = [elder["name"] for elder in elder_list]
    assert sample_elder_data["name"] in names


@pytest.mark.slow
@pytest.mark.integration
def test_heavy_elder_processing():
    """重い処理のテスト例"""
    import time

    time.sleep(0.1)  # 重い処理をシミュレート

    # 大量データ処理をシミュレート
    elder_data = [{"id": i, "level": i * 10} for i in range(100)]
    processed = [elder for elder in elder_data if elder["level"] > 500]
    # レベル510以上 (i=51-99) なので49個が正しい
    assert len(processed) == 49


@pytest.mark.skip(reason="実装中のため一時的にスキップ")
def test_future_feature():
    """将来実装予定の機能テスト"""
    pass


@pytest.mark.xfail(reason="既知のバグ - Issue #123")
def test_known_bug():
    """既知のバグのテスト（失敗予定）"""
    assert False  # 既知のバグによる失敗


# =============================================================================
# 実習5: 例外処理テスト
# =============================================================================


def divide_elder_experience(total_exp: int, elder_count: int) -> float:
    """経験値を複数エルダーに分割"""
    if elder_count <= 0:
        raise ValueError("エルダー数は1以上である必要があります")
    return total_exp / elder_count


def test_divide_experience_success():
    """正常な経験値分割テスト"""
    result = divide_elder_experience(1000, 4)
    assert result == 250.0


def test_divide_experience_zero_elders():
    """ゼロ除算例外テスト"""
    with pytest.raises(ValueError, match="エルダー数は1以上"):
        divide_elder_experience(1000, 0)


def test_divide_experience_negative_elders():
    """負の数例外テスト"""
    with pytest.raises(ValueError):
        divide_elder_experience(1000, -1)


# =============================================================================
# 実習6: アサーション詳細
# =============================================================================


def test_assertion_examples():
    """様々なアサーション例"""
    # 等価性
    assert 2 + 2 == 4

    # 真偽値
    assert True
    assert not False

    # 包含関係
    assert "Elder" in "Claude Elder"
    assert 3 in [1, 2, 3, 4]

    # 近似値 (浮動小数点)
    assert 0.1 + 0.2 == pytest.approx(0.3)

    # 型チェック
    assert isinstance("Hello", str)
    assert isinstance(42, int)


if __name__ == "__main__":
    # このスクリプトを直接実行した場合の動作例
    print("🧪 pytest基礎実習へようこそ！")
    print("\n以下のコマンドで実習を開始してください：")
    print("pytest training/week2/day1_pytest/pytest_basics_tutorial.py -v")
    print("\n特定のマークのテストのみ実行：")
    print("pytest -m unit")
    print("pytest -m integration")
    print("pytest -m 'not slow'")
