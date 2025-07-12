"""
Elder Flow Game UI - CUIゲーム風インターフェース
エルダーズギルドのファンタジー世界観をCUIで表現
"""
import os
import sys
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio

# Elder Flowシステムとの連携
from libs.elder_flow_violation_detector import ElderFlowViolationDetector
from libs.elder_flow_violation_types import ViolationType, ViolationSeverity
from libs.elder_flow_hourly_audit import HourlyAuditSystem
from libs.elder_flow_pdca_engine import PDCAEngine
from libs.elder_flow_realtime_monitor import RealtimeMonitoringSystem


class GameColor(Enum):
    """ゲーム用カラーコード"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # 基本色
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # 背景色
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'

    # エルダーズギルド専用色
    ELDER_GOLD = '\033[93m'
    SAGE_BLUE = '\033[96m'
    KNIGHT_SILVER = '\033[97m'
    CRITICAL_RED = '\033[91m'


class UIElement:
    """UI要素の基底クラス"""

    @staticmethod
    def colorize(text: str, color: GameColor, bold: bool = False) -> str:
        """テキストに色付け"""
        result = color.value + text + GameColor.RESET.value
        if bold:
            result = GameColor.BOLD.value + result
        return result

    @staticmethod
    def frame_text(text: str, width: int = 60, char: str = '═') -> str:
        """テキストを枠で囲む"""
        lines = text.split('\n')
        framed = []

        # 上枠
        framed.append('╔' + char * (width - 2) + '╗')

        # 内容
        for line in lines:
            padding = width - len(line) - 4
            left_pad = padding // 2
            right_pad = padding - left_pad
            framed.append('║ ' + ' ' * left_pad + line + ' ' * right_pad + ' ║')

        # 下枠
        framed.append('╚' + char * (width - 2) + '╝')

        return '\n'.join(framed)

    @staticmethod
    def progress_bar(current: int, total: int, width: int = 40, char: str = '█') -> str:
        """プログレスバー生成"""
        if total == 0:
            return '[' + ' ' * width + '] 0%'

        progress = current / total
        filled = int(width * progress)
        empty = width - filled

        bar = '[' + char * filled + ' ' * empty + ']'
        percentage = f' {int(progress * 100)}%'

        return bar + percentage


@dataclass
class PlayerStats:
    """プレイヤー（開発者）の統計"""
    level: int = 1
    exp: int = 0
    violations_fixed: int = 0
    tests_written: int = 0
    commits_made: int = 0
    elder_approval_rate: float = 0.0

    def calculate_level(self) -> int:
        """経験値からレベルを計算"""
        return max(1, int((self.exp / 100) ** 0.5) + 1)

    def add_exp(self, amount: int, reason: str = ""):
        """経験値を追加"""
        self.exp += amount
        old_level = self.level
        self.level = self.calculate_level()

        if self.level > old_level:
            return f"🎉 レベルアップ! Lv.{old_level} → Lv.{self.level} ({reason})"
        return f"+{amount} EXP ({reason})"


class ElderFlowGameUI:
    """Elder Flow ゲーム風CUIメインクラス"""

    def __init__(self):
        self.detector = ElderFlowViolationDetector()
        self.audit_system = HourlyAuditSystem()
        self.pdca_engine = PDCAEngine()
        self.monitor = RealtimeMonitoringSystem()

        self.player_stats = PlayerStats()
        self.current_screen = "main_menu"
        self.running = True

        # ゲーム状態
        self.elder_mood = "neutral"  # happy, neutral, angry
        self.current_quest = None
        self.achievements = []

    def clear_screen(self):
        """画面クリア"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """ヘッダー表示"""
        header = f"""
{UIElement.colorize('🏛️ Elder Flow Game Interface 🏛️', GameColor.ELDER_GOLD, True)}
{UIElement.colorize('═' * 60, GameColor.ELDER_GOLD)}
{UIElement.colorize(f'Developer: Lv.{self.player_stats.level}', GameColor.SAGE_BLUE)} | {UIElement.colorize(f'EXP: {self.player_stats.exp}', GameColor.GREEN)} | {UIElement.colorize(f'Elder Mood: {self.get_elder_mood_display()}', self.get_elder_mood_color())}
{UIElement.colorize('═' * 60, GameColor.ELDER_GOLD)}
"""
        print(header)

    def get_elder_mood_display(self) -> str:
        """エルダーの気分表示"""
        mood_map = {
            "happy": "😊 満足",
            "neutral": "😐 普通",
            "angry": "😡 不満"
        }
        return mood_map.get(self.elder_mood, "😐 普通")

    def get_elder_mood_color(self) -> GameColor:
        """エルダーの気分に応じた色"""
        mood_colors = {
            "happy": GameColor.GREEN,
            "neutral": GameColor.YELLOW,
            "angry": GameColor.RED
        }
        return mood_colors.get(self.elder_mood, GameColor.YELLOW)

    def show_main_menu(self):
        """メインメニュー表示"""
        menu_text = f"""
{UIElement.colorize('🌟 エルダーズギルド 開発者ポータル 🌟', GameColor.ELDER_GOLD, True)}

{UIElement.colorize('1.', GameColor.CYAN)} 🕵️‍♂️ 違反検知システム
{UIElement.colorize('2.', GameColor.CYAN)} ⏰ 毎時監査ダッシュボード
{UIElement.colorize('3.', GameColor.CYAN)} 🔄 PDCA改善サイクル
{UIElement.colorize('4.', GameColor.CYAN)} 🛡️ リアルタイム監視
{UIElement.colorize('5.', GameColor.CYAN)} 📊 統計・実績
{UIElement.colorize('6.', GameColor.CYAN)} 🎮 ミニゲーム
{UIElement.colorize('7.', GameColor.CYAN)} ⚙️  設定
{UIElement.colorize('0.', GameColor.RED)} 🚪 終了

{UIElement.colorize('選択してください:', GameColor.WHITE)}"""

        print(UIElement.frame_text(menu_text))

    def show_violation_detector(self):
        """違反検知システム画面"""
        self.clear_screen()
        self.print_header()

        detector_ui = f"""
{UIElement.colorize('🕵️‍♂️ Elder Flow 違反検知システム', GameColor.CRITICAL_RED, True)}

{UIElement.colorize('現在の違反検知状況:', GameColor.YELLOW)}
"""
        print(detector_ui)

        # シミュレートされた違反チェック
        violations = [
            ("🔍 コード品質チェック", random.choice([True, False])),
            ("🔒 セキュリティスキャン", random.choice([True, False])),
            ("📋 ドキュメント確認", random.choice([True, False])),
            ("🧪 テストカバレッジ", random.choice([True, False]))
        ]

        for check_name, passed in violations:
            status = UIElement.colorize("✅ 合格", GameColor.GREEN) if passed else UIElement.colorize("❌ 違反", GameColor.RED)
            print(f"  {check_name}: {status}")

        # 統計表示
        total_checks = len(violations)
        passed_checks = sum(1 for _, passed in violations if passed)
        success_rate = (passed_checks / total_checks) * 100

        print(f"\n{UIElement.colorize('総合スコア:', GameColor.YELLOW)} {UIElement.progress_bar(passed_checks, total_checks)}")
        print(f"{UIElement.colorize(f'成功率: {success_rate:.1f}%', GameColor.GREEN if success_rate >= 80 else GameColor.RED)}")

        # エルダーのコメント
        if success_rate >= 90:
            comment = UIElement.colorize("🏆 グランドエルダーmaru: 「素晴らしい品質です！」", GameColor.GREEN)
            self.elder_mood = "happy"
        elif success_rate >= 70:
            comment = UIElement.colorize("💭 クロードエルダー: 「もう少し改善が必要ですね」", GameColor.YELLOW)
            self.elder_mood = "neutral"
        else:
            comment = UIElement.colorize("⚠️ インシデント賢者: 「緊急対応が必要です！」", GameColor.RED)
            self.elder_mood = "angry"

        print(f"\n{comment}")

        input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    def show_audit_dashboard(self):
        """監査ダッシュボード画面"""
        self.clear_screen()
        self.print_header()

        dashboard_ui = f"""
{UIElement.colorize('⏰ 毎時監査ダッシュボード', GameColor.SAGE_BLUE, True)}

{UIElement.colorize('今日の監査サマリー:', GameColor.YELLOW)}
"""
        print(dashboard_ui)

        # 監査結果のシミュレーション
        audit_results = [
            ("包括的スキャン", random.randint(0, 5), "件の問題"),
            ("アクティブ違反", random.randint(0, 3), "件"),
            ("統計分析", "改善傾向" if random.choice([True, False]) else "要注意", ""),
            ("レポート生成", "完了", "")
        ]

        for audit_type, result, unit in audit_results:
            if isinstance(result, int) and result > 0:
                color = GameColor.RED if result > 2 else GameColor.YELLOW
            else:
                color = GameColor.GREEN

            print(f"  📋 {audit_type}: {UIElement.colorize(str(result) + unit, color)}")

        # 次回監査予定
        next_audit_minutes = random.randint(5, 45)
        print(f"\n⏳ {UIElement.colorize(f'次回監査まで: {next_audit_minutes}分', GameColor.CYAN)}")

        # プログレスバー表示
        progress = (60 - next_audit_minutes) / 60
        bar = UIElement.progress_bar(int(progress * 100), 100, 30, '▓')
        print(f"   {bar}")

        input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    def show_pdca_cycle(self):
        """PDCAサイクル画面"""
        self.clear_screen()
        self.print_header()

        pdca_ui = f"""
{UIElement.colorize('🔄 PDCA改善サイクル', GameColor.MAGENTA, True)}

{UIElement.colorize('現在のサイクル状況:', GameColor.YELLOW)}
"""
        print(pdca_ui)

        # PDCAフェーズの表示
        phases = [
            ("📋 Plan", "計画策定", random.choice(["完了", "実行中", "待機中"])),
            ("⚡ Do", "改善実行", random.choice(["完了", "実行中", "待機中"])),
            ("🔍 Check", "効果測定", random.choice(["完了", "実行中", "待機中"])),
            ("🔧 Act", "標準化", random.choice(["完了", "実行中", "待機中"]))
        ]

        for phase, description, status in phases:
            if status == "完了":
                status_display = UIElement.colorize("✅ 完了", GameColor.GREEN)
            elif status == "実行中":
                status_display = UIElement.colorize("🔄 実行中", GameColor.YELLOW)
            else:
                status_display = UIElement.colorize("⏸️ 待機中", GameColor.BLUE)

            print(f"  {phase} {description}: {status_display}")

        # 改善メトリクス
        print(f"\n{UIElement.colorize('改善メトリクス:', GameColor.YELLOW)}")
        metrics = [
            ("違反発生率", random.randint(0, 10), "件/時"),
            ("自動修正率", random.randint(70, 95), "%"),
            ("平均修復時間", random.randint(15, 45), "分")
        ]

        for metric, value, unit in metrics:
            if "率" in metric:
                color = GameColor.GREEN if value >= 80 else GameColor.YELLOW if value >= 60 else GameColor.RED
            else:
                color = GameColor.GREEN if value <= 20 else GameColor.YELLOW if value <= 35 else GameColor.RED

            print(f"  📊 {metric}: {UIElement.colorize(f'{value}{unit}', color)}")

        input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    def show_realtime_monitor(self):
        """リアルタイム監視画面"""
        self.clear_screen()
        self.print_header()

        monitor_ui = f"""
{UIElement.colorize('🛡️ リアルタイム監視システム', GameColor.KNIGHT_SILVER, True)}

{UIElement.colorize('監視状況 (リアルタイム更新中...):', GameColor.YELLOW)}
"""
        print(monitor_ui)

        # リアルタイム監視のシミュレーション
        for i in range(10):
            timestamp = datetime.now().strftime("%H:%M:%S")
            events = [
                "ファイル変更検知",
                "Gitフック実行",
                "コマンド実行監視",
                "自動修正実行",
                "違反検知"
            ]

            event = random.choice(events)
            status = random.choice(["正常", "警告", "違反"])

            if status == "正常":
                color = GameColor.GREEN
                icon = "✅"
            elif status == "警告":
                color = GameColor.YELLOW
                icon = "⚠️"
            else:
                color = GameColor.RED
                icon = "🚨"

            print(f"  [{timestamp}] {icon} {event}: {UIElement.colorize(status, color)}")
            time.sleep(0.5)

        input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    def show_statistics(self):
        """統計・実績画面"""
        self.clear_screen()
        self.print_header()

        stats_ui = f"""
{UIElement.colorize('📊 統計・実績', GameColor.ELDER_GOLD, True)}

{UIElement.colorize('あなたの開発者ステータス:', GameColor.YELLOW)}
"""
        print(stats_ui)

        # プレイヤー統計
        stats = [
            ("レベル", self.player_stats.level, ""),
            ("経験値", self.player_stats.exp, "EXP"),
            ("修正した違反", self.player_stats.violations_fixed, "件"),
            ("書いたテスト", self.player_stats.tests_written, "個"),
            ("コミット数", self.player_stats.commits_made, "回"),
            ("エルダー承認率", f"{self.player_stats.elder_approval_rate:.1f}", "%")
        ]

        for stat_name, value, unit in stats:
            print(f"  🎯 {stat_name}: {UIElement.colorize(f'{value}{unit}', GameColor.CYAN)}")

        # 実績システム
        print(f"\n{UIElement.colorize('🏆 実績 (Achievements):', GameColor.YELLOW)}")
        achievements = [
            ("🥇 初回コミット", "最初のコミットを実行"),
            ("🛡️ 守護者", "10個の違反を修正"),
            ("🧪 テストマスター", "50個のテストを作成"),
            ("⚡ スピードデバッガー", "1日で5個の違反を修正"),
            ("🏛️ エルダー認定", "承認率90%を達成")
        ]

        for achievement, description in achievements:
            unlocked = random.choice([True, False])
            status = UIElement.colorize("✅ 達成", GameColor.GREEN) if unlocked else UIElement.colorize("🔒 未達成", GameColor.DIM)
            print(f"  {achievement} {description}: {status}")

        input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    def show_mini_games(self):
        """ミニゲーム画面"""
        self.clear_screen()
        self.print_header()

        games_ui = f"""
{UIElement.colorize('🎮 Elder Flow ミニゲーム', GameColor.MAGENTA, True)}

{UIElement.colorize('1.', GameColor.CYAN)} 🎯 違反撃退ゲーム
{UIElement.colorize('2.', GameColor.CYAN)} 🧩 コードパズル
{UIElement.colorize('3.', GameColor.CYAN)} ⚡ スピードテスト作成
{UIElement.colorize('4.', GameColor.CYAN)} 🏆 エルダー承認チャレンジ
{UIElement.colorize('0.', GameColor.RED)} 🔙 戻る

{UIElement.colorize('選択してください:', GameColor.WHITE)}"""

        print(UIElement.frame_text(games_ui))

        choice = input().strip()

        if choice == "1":
            self.violation_shooter_game()
        elif choice == "2":
            self.code_puzzle_game()
        elif choice == "3":
            self.speed_test_game()
        elif choice == "4":
            self.elder_approval_challenge()

    def violation_shooter_game(self):
        """違反撃退ゲーム"""
        self.clear_screen()
        print(UIElement.colorize("🎯 違反撃退ゲーム開始！", GameColor.CRITICAL_RED, True))
        print("違反が出現します。正しい修正方法を選んでください！\n")

        violations = [
            {
                "violation": "本番コードにMockオブジェクトが残っている",
                "options": ["A) 無視する", "B) 実際の実装に置き換える", "C) コメントアウトする"],
                "correct": "B",
                "explanation": "本番コードのMockは実際の実装に置き換える必要があります"
            },
            {
                "violation": "テストカバレッジが80%しかない",
                "options": ["A) 十分だから放置", "B) テストを追加して95%以上にする", "C) カバレッジツールを無効化"],
                "correct": "B",
                "explanation": "Elder Flowでは95%以上のカバレッジが必要です"
            },
            {
                "violation": "dockerコマンドを直接実行している",
                "options": ["A) そのまま続行", "B) sg docker -c を使用する", "C) sudoを追加する"],
                "correct": "B",
                "explanation": "Docker権限問題を避けるため sg docker -c を使用します"
            }
        ]

        score = 0
        for i, violation in enumerate(violations, 1):
            print(f"{UIElement.colorize(f'問題 {i}:', GameColor.YELLOW)} {violation['violation']}")
            for option in violation['options']:
                print(f"  {option}")

            answer = input(f"\n{UIElement.colorize('答え:', GameColor.CYAN)} ").strip().upper()

            if answer == violation['correct']:
                print(UIElement.colorize("✅ 正解！", GameColor.GREEN))
                score += 10
                self.player_stats.add_exp(5, "違反修正")
            else:
                print(UIElement.colorize("❌ 不正解", GameColor.RED))

            print(f"{UIElement.colorize('解説:', GameColor.BLUE)} {violation['explanation']}\n")
            time.sleep(2)

        print(f"{UIElement.colorize(f'最終スコア: {score}/30', GameColor.ELDER_GOLD, True)}")
        input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    def code_puzzle_game(self):
        """コードパズルゲーム"""
        self.clear_screen()
        print(UIElement.colorize("🧩 コードパズル", GameColor.SAGE_BLUE, True))
        print("正しいElderFlow開発の順序を並べてください！\n")

        correct_order = [
            "1. 4賢者への相談",
            "2. テストファースト（TDD）",
            "3. 実装",
            "4. 品質チェック",
            "5. コミット&プッシュ"
        ]

        shuffled = correct_order.copy()
        random.shuffle(shuffled)

        print("現在の順序:")
        for i, step in enumerate(shuffled, 1):
            print(f"  {i}. {step}")

        print(f"\n{UIElement.colorize('正しい順序を番号で入力してください (例: 3,1,4,2,5):', GameColor.CYAN)}")
        user_input = input().strip()

        try:
            user_order = [int(x.strip()) - 1 for x in user_input.split(',')]
            reordered = [shuffled[i] for i in user_order]

            if reordered == correct_order:
                print(UIElement.colorize("🎉 正解！完璧なElder Flowです！", GameColor.GREEN))
                self.player_stats.add_exp(15, "パズル解決")
            else:
                print(UIElement.colorize("❌ 不正解。正しい順序を覚えましょう。", GameColor.RED))
                print("\n正解:")
                for step in correct_order:
                    print(f"  {step}")
        except:
            print(UIElement.colorize("❌ 入力形式が正しくありません", GameColor.RED))

        input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    def speed_test_game(self):
        """スピードテスト作成ゲーム"""
        self.clear_screen()
        print(UIElement.colorize("⚡ スピードテスト作成チャレンジ", GameColor.YELLOW, True))
        print("30秒以内にできるだけ多くのテストケースを考えてください！\n")

        function_to_test = """
def calculate_tax(price, tax_rate):
    return price * (1 + tax_rate)
"""

        print(f"テスト対象関数:\n{UIElement.colorize(function_to_test, GameColor.CYAN)}")
        print(f"{UIElement.colorize('テストケースを1行ずつ入力してください (30秒)', GameColor.YELLOW)}")
        print("例: calculate_tax(100, 0.1) == 110")

        test_cases = []
        start_time = time.time()

        while time.time() - start_time < 30:
            remaining = 30 - int(time.time() - start_time)
            try:
                test_case = input(f"[残り{remaining}秒] テストケース: ").strip()
                if test_case:
                    test_cases.append(test_case)
            except KeyboardInterrupt:
                break

        score = len(test_cases) * 5
        print(f"\n{UIElement.colorize(f'作成したテストケース: {len(test_cases)}個', GameColor.GREEN)}")
        print(f"{UIElement.colorize(f'スコア: {score}点', GameColor.ELDER_GOLD)}")

        if len(test_cases) >= 5:
            exp_gained = self.player_stats.add_exp(20, "スピードテスト")
            print(f"{UIElement.colorize(exp_gained, GameColor.GREEN)}")

        input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    def elder_approval_challenge(self):
        """エルダー承認チャレンジ"""
        self.clear_screen()
        print(UIElement.colorize("🏆 エルダー承認チャレンジ", GameColor.ELDER_GOLD, True))
        print("グランドエルダーmaruの厳しい審査に挑戦！\n")

        challenges = [
            {
                "challenge": "完了の定義を述べよ",
                "answer": "本番環境で実際に動作する完全な実装のみが完了",
                "keyword": "本番環境"
            },
            {
                "challenge": "Elder Flowの階層の頂点は？",
                "answer": "グランドエルダーmaru",
                "keyword": "maru"
            },
            {
                "challenge": "テストカバレッジの最低基準は？",
                "answer": "95%以上",
                "keyword": "95"
            }
        ]

        correct_answers = 0
        for i, challenge in enumerate(challenges, 1):
            print(f"{UIElement.colorize(f'問題 {i}:', GameColor.YELLOW)} {challenge['challenge']}")
            answer = input(f"{UIElement.colorize('答え:', GameColor.CYAN)} ").strip()

            if challenge['keyword'].lower() in answer.lower():
                print(UIElement.colorize("✅ グランドエルダーmaruが承認！", GameColor.GREEN))
                correct_answers += 1
            else:
                print(UIElement.colorize("❌ 承認されませんでした", GameColor.RED))
                print(f"{UIElement.colorize('正解:', GameColor.BLUE)} {challenge['answer']}")
            print()

        approval_rate = (correct_answers / len(challenges)) * 100
        self.player_stats.elder_approval_rate = approval_rate

        if approval_rate >= 80:
            print(UIElement.colorize("🎉 エルダー認定を獲得！", GameColor.ELDER_GOLD, True))
            exp_gained = self.player_stats.add_exp(30, "エルダー認定")
            print(f"{UIElement.colorize(exp_gained, GameColor.GREEN)}")
        else:
            print(UIElement.colorize("📚 もっと学習が必要です", GameColor.YELLOW))

        input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    def show_settings(self):
        """設定画面"""
        self.clear_screen()
        self.print_header()

        settings_ui = f"""
{UIElement.colorize('⚙️ 設定', GameColor.BLUE, True)}

{UIElement.colorize('1.', GameColor.CYAN)} 🎨 カラーテーマ変更
{UIElement.colorize('2.', GameColor.CYAN)} 🔊 サウンド設定
{UIElement.colorize('3.', GameColor.CYAN)} 📊 統計リセット
{UIElement.colorize('4.', GameColor.CYAN)} 💾 データエクスポート
{UIElement.colorize('0.', GameColor.RED)} 🔙 戻る

{UIElement.colorize('選択してください:', GameColor.WHITE)}"""

        print(UIElement.frame_text(settings_ui))

        choice = input().strip()

        if choice == "1":
            print(UIElement.colorize("🎨 カラーテーマ変更機能は開発中です", GameColor.YELLOW))
        elif choice == "2":
            print(UIElement.colorize("🔊 サウンド設定機能は開発中です", GameColor.YELLOW))
        elif choice == "3":
            confirm = input(UIElement.colorize("統計をリセットしますか？ (y/N): ", GameColor.RED))
            if confirm.lower() == 'y':
                self.player_stats = PlayerStats()
                print(UIElement.colorize("✅ 統計をリセットしました", GameColor.GREEN))
        elif choice == "4":
            print(UIElement.colorize("💾 データエクスポート機能は開発中です", GameColor.YELLOW))

        if choice != "0":
            input(f"\n{UIElement.colorize('Enterキーで戻る...', GameColor.CYAN)}")

    async def run(self):
        """メインゲームループ"""
        while self.running:
            self.clear_screen()
            self.print_header()
            self.show_main_menu()

            choice = input().strip()

            if choice == "1":
                self.show_violation_detector()
            elif choice == "2":
                self.show_audit_dashboard()
            elif choice == "3":
                self.show_pdca_cycle()
            elif choice == "4":
                self.show_realtime_monitor()
            elif choice == "5":
                self.show_statistics()
            elif choice == "6":
                self.show_mini_games()
            elif choice == "7":
                self.show_settings()
            elif choice == "0":
                print(UIElement.colorize("👋 Elder Flow Game UIを終了します", GameColor.CYAN))
                self.running = False
            else:
                print(UIElement.colorize("❌ 無効な選択です", GameColor.RED))
                time.sleep(1)


# CLI起動用
async def main():
    """ゲームUI起動"""
    print(UIElement.colorize("🎮 Elder Flow Game UI 起動中...", GameColor.ELDER_GOLD))
    time.sleep(2)

    game = ElderFlowGameUI()
    await game.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{UIElement.colorize('🎮 ゲームを終了しました', GameColor.CYAN)}")
    except Exception as e:
        print(f"{UIElement.colorize(f'❌ エラー: {e}', GameColor.RED)}")
