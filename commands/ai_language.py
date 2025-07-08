#!/usr/bin/env python3
"""
AI Language Command - 言語設定コマンド

AI Companyシステムの言語設定を管理する
"""

import sys
import json
from pathlib import Path

# パスの設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

from core.config import get_config
from libs.localization_manager import get_localization, set_language, t


def show_current_language():
    """現在の言語設定を表示"""
    loc = get_localization()
    config = get_config()
    
    print(f"現在の言語設定:")
    print(f"  言語: {loc.get_current_language()}")
    print(f"  サポート言語: {', '.join(loc.get_supported_languages())}")
    print(f"  タイムゾーン: {config.language.timezone}")
    print(f"  日付フォーマット: {config.language.date_format}")
    print(f"  時刻フォーマット: {config.language.time_format}")


def change_language(new_language: str):
    """言語を変更"""
    loc = get_localization()
    
    if new_language not in loc.get_supported_languages():
        print(f"エラー: サポートされていない言語です: {new_language}")
        print(f"サポート言語: {', '.join(loc.get_supported_languages())}")
        return False
    
    # 言語設定を変更
    if set_language(new_language):
        print(f"言語を {new_language} に変更しました")
        
        # 設定ファイルも更新
        config = get_config()
        config.language.default_language = new_language
        
        # language.jsonファイルを更新
        language_config_file = config.config_dir / 'language.json'
        try:
            with open(language_config_file, 'r', encoding='utf-8') as f:
                lang_config = json.load(f)
            
            lang_config['default_language'] = new_language
            
            with open(language_config_file, 'w', encoding='utf-8') as f:
                json.dump(lang_config, f, indent=2, ensure_ascii=False)
            
            print("設定ファイルを更新しました")
        except Exception as e:
            print(f"警告: 設定ファイルの更新に失敗しました: {e}")
        
        return True
    else:
        print(f"言語の変更に失敗しました: {new_language}")
        return False


def test_messages():
    """メッセージのテスト表示"""
    print("\nメッセージテスト:")
    print(f"システム開始: {t('system.startup')}")
    print(f"ワーカー開始: {t('worker.started')}")
    print(f"タスク完了: {t('worker.task_completed')}")
    print(f"Slack通知送信: {t('slack.notification_sent')}")
    print(f"設定読み込み: {t('config.loaded')}")


def show_help():
    """ヘルプメッセージを表示"""
    print("AI Language Command - 言語設定管理")
    print("")
    print("使用方法:")
    print("  ai-language [コマンド] [オプション]")
    print("")
    print("コマンド:")
    print("  show, status    現在の言語設定を表示")
    print("  set <言語>      言語を変更（ja, en）")
    print("  test           メッセージの翻訳テスト")
    print("  help           このヘルプを表示")
    print("")
    print("例:")
    print("  ai-language show       # 現在の設定を表示")
    print("  ai-language set ja     # 日本語に変更")
    print("  ai-language set en     # 英語に変更")
    print("  ai-language test       # 翻訳テスト")


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        show_current_language()
        return
    
    command = sys.argv[1].lower()
    
    if command in ['show', 'status']:
        show_current_language()
    
    elif command == 'set':
        if len(sys.argv) < 3:
            print("エラー: 言語を指定してください")
            print("例: ai-language set ja")
            return
        
        new_language = sys.argv[2].lower()
        change_language(new_language)
    
    elif command == 'test':
        test_messages()
    
    elif command in ['help', '-h', '--help']:
        show_help()
    
    else:
        print(f"不明なコマンド: {command}")
        show_help()


if __name__ == "__main__":
    main()