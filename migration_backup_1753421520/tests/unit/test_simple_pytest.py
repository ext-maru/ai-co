"""簡単なpytestテスト - OSS移行検証用"""

def test_simple_addition():
    """シンプルな加算テスト"""
    assert 1 + 1 == 2

def test_simple_string():
    """シンプルな文字列テスト"""
    assert "hello" + " " + "world" == "hello world"

def test_simple_list():
    """シンプルなリストテスト"""
    items = [1, 2, 3]
    assert len(items) == 3
    assert items[0] == 1