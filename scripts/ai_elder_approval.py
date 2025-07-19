#!/usr/bin/env python3
"""
AI Elder Approval Request System
グランドエルダーmaruへの承認申請システム
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent


def save_approval_request(request_data):
    """承認申請をファイルとPostgreSQLに保存"""
    # ファイル保存
    approval_dir = PROJECT_ROOT / "knowledge_base" / "elder_approvals"
    approval_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"approval_request_{timestamp}.json"
    filepath = approval_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)

    # PostgreSQL保存
    db_url = "postgresql://aicompany@localhost:5432/ai_company_grimoire"
    spell_name = f"Approval_Request_{timestamp}"

    content = json.dumps(request_data, ensure_ascii=False, indent=2)
    content_escaped = content.replace("'", "''")

    tags = ["approval", "request", "grand-elder", request_data["type"]]
    tags_sql = "ARRAY[" + ",".join([f"'{tag}'" for tag in tags]) + "]"

    sql = f"""
    INSERT INTO knowledge_grimoire (
        spell_name, content, spell_type, magic_school,
        tags, power_level, is_eternal, created_at, updated_at
    )
    VALUES (
        '{spell_name}',
        '{content_escaped}',
        'approval_request',
        'elder_magic',
        {tags_sql},
        8,
        false,
        NOW(),
        NOW()
    );
    """

    subprocess.run(["psql", db_url, "-c", sql], capture_output=True)

    return filepath


def create_approval_request(
    request_type, title, description, details=None, urgency="normal"
):
    """承認申請を作成"""
    request_data = {
        "request_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().isoformat(),
        "requester": "Claude Elder",
        "type": request_type,
        "urgency": urgency,
        "title": title,
        "description": description,
        "details": details or {},
        "status": "pending",
        "grand_elder_decision": None,
        "decision_timestamp": None,
        "notes": [],
    }

    return request_data


def format_approval_display(request_data):
    """承認申請を見やすく表示"""
    urgency_emoji = {"critical": "🚨", "high": "⚡", "normal": "📋", "low": "💭"}

    type_emoji = {
        "system_change": "🔧",
        "eternal_knowledge": "📜",
        "hierarchy_change": "👑",
        "rule_change": "📏",
        "emergency": "🚨",
        "feature": "✨",
        "other": "📝",
    }

    print("\n" + "=" * 60)
    print(f"{urgency_emoji.get(request_data['urgency'], '📋')} **承認申請書**")
    print("=" * 60)
    print(f"申請ID: {request_data['request_id']}")
    print(f"申請者: {request_data['requester']}")
    print(f"種別: {type_emoji.get(request_data['type'], '📝')} {request_data['type']}")
    print(f"緊急度: {request_data['urgency']}")
    print(f"申請日時: {request_data['timestamp']}")
    print("\n**件名**: " + request_data["title"])
    print("\n**説明**:")
    print(request_data["description"])

    if request_data["details"]:
        print("\n**詳細**:")
        for key, value in request_data["details"].items():
            print(f"  - {key}: {value}")

    print("\n" + "=" * 60)
    print("グランドエルダーmaruへの承認申請が作成されました。")
    print("=" * 60)


def list_pending_approvals():
    """保留中の承認申請一覧を表示"""
    approval_dir = PROJECT_ROOT / "knowledge_base" / "elder_approvals"
    if not approval_dir.exists():
        print("承認申請はありません。")
        return

    pending_requests = []
    for file in approval_dir.glob("approval_request_*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("status") == "pending":
                pending_requests.append(data)

    if not pending_requests:
        print("保留中の承認申請はありません。")
        return

    print("\n📋 保留中の承認申請一覧:")
    print("=" * 60)
    for req in sorted(pending_requests, key=lambda x: x["timestamp"], reverse=True):
        urgency_mark = "🚨" if req["urgency"] == "critical" else ""
        print(f"{urgency_mark} [{req['request_id']}] {req['title']}")
        print(f"   種別: {req['type']} | 緊急度: {req['urgency']}")
        print(f"   申請日時: {req['timestamp']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="グランドエルダーmaruへの承認申請システム")

    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # 新規申請
    new_parser = subparsers.add_parser("new", help="新規承認申請")
    new_parser.add_argument(
        "--type",
        "-t",
        required=True,
        choices=[
            "system_change",
            "eternal_knowledge",
            "hierarchy_change",
            "rule_change",
            "emergency",
            "feature",
            "other",
        ],
        help="申請種別",
    )
    new_parser.add_argument("--title", required=True, help="申請タイトル")
    new_parser.add_argument("--description", "-d", required=True, help="申請内容の説明")
    new_parser.add_argument(
        "--urgency",
        "-u",
        default="normal",
        choices=["critical", "high", "normal", "low"],
        help="緊急度",
    )
    new_parser.add_argument("--details", "-D", nargs="*", help="追加詳細 (key=value形式)")

    # 一覧表示
    list_parser = subparsers.add_parser("list", help="保留中の承認申請一覧")

    # クイック申請（よく使うパターン）
    quick_parser = subparsers.add_parser("quick", help="クイック承認申請")
    quick_parser.add_argument(
        "pattern", choices=["eternal", "system", "emergency", "rule"], help="クイックパターン"
    )
    quick_parser.add_argument("title", help="タイトル")
    quick_parser.add_argument("description", help="説明")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "new":
        # 詳細情報をパース
        details = {}
        if args.details:
            for detail in args.details:
                if "=" in detail:
                    key, value = detail.split("=", 1)
                    details[key] = value

        # 承認申請作成
        request = create_approval_request(
            args.type, args.title, args.description, details, args.urgency
        )

        # 保存
        filepath = save_approval_request(request)

        # 表示
        format_approval_display(request)
        print(f"\n💾 保存先: {filepath}")

    elif args.command == "list":
        list_pending_approvals()

    elif args.command == "quick":
        # クイックパターン
        patterns = {
            "eternal": {
                "type": "eternal_knowledge",
                "urgency": "high",
                "template": "永続知識への追加申請",
            },
            "system": {
                "type": "system_change",
                "urgency": "normal",
                "template": "システム変更申請",
            },
            "emergency": {
                "type": "emergency",
                "urgency": "critical",
                "template": "緊急対応申請",
            },
            "rule": {"type": "rule_change", "urgency": "normal", "template": "ルール変更申請"},
        }

        pattern = patterns[args.pattern]
        request = create_approval_request(
            pattern["type"],
            args.title,
            args.description,
            {"template": pattern["template"]},
            pattern["urgency"],
        )

        filepath = save_approval_request(request)
        format_approval_display(request)
        print(f"\n💾 保存先: {filepath}")


if __name__ == "__main__":
    main()
