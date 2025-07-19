#!/usr/bin/env python3
from pathlib import Path

# PMWorkerのパス
pm_path = Path("/home/aicompany/ai_co/workers/pm_worker.py")

# 現在の内容を読む
content = pm_path.read_text()

# 修正前の状態を確認
if (
    "if self.git_flow.commit_changes(None, new_files, use_best_practices=True):"
    in content
):
    print("⚠️ PMWorkerがまだ修正されていません。修正を適用します...")

    # 修正を適用
    lines = content.split("\n")
    new_lines = []

    for i, line in enumerate(lines):
        if (
            "if self.git_flow.commit_changes(None, new_files, use_best_practices=True):"
            in line
        ):
            indent = " " * (len(line) - len(line.lstrip()))
            # コメント行を修正
            if i > 0 and "ベストプラクティス対応" in lines[i - 1]:
                new_lines[-1] = f"{indent}# ファイルをコミット（ベストプラクティス対応）"
            # commit_message定義を追加
            new_lines.append(
                f'{indent}commit_message = f"Task {{task_id}}: {{git_result_data["summary"]}}"[:100]'
            )
            # 修正した行を追加
            new_lines.append(line.replace("None", "commit_message"))
        else:
            new_lines.append(line)

    # ファイルを保存
    pm_path.write_text("\n".join(new_lines))
    print("✅ 修正を適用しました！")
else:
    print("✅ PMWorkerは既に修正済みです")

# 修正後の確認
content = pm_path.read_text()
lines = content.split("\n")

print("\n=== 修正後の130-140行目 ===")
for i in range(129, min(140, len(lines))):
    if "commit_message" in lines[i] or "use_best_practices" in lines[i]:
        print(f"{i+1}: >>> {lines[i]}")
    else:
        print(f"{i+1}:     {lines[i]}")

# 統合状態の確認
print("\n=== 統合状態 ===")
has_commit_def = 'commit_message = f"Task {task_id}' in content
has_best_practices = "use_best_practices=True" in content

print(f"commit_message定義: {'✅ あり' if has_commit_def else '❌ なし'}")
print(f"use_best_practices設定: {'✅ あり' if has_best_practices else '❌ なし'}")

if has_commit_def and has_best_practices:
    print("\n🎉 ベストプラクティス統合が完了しました！")
