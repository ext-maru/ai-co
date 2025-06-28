#!/bin/bash
# prepare_github_deploy_key.sh
# GitHub Deploy Key用SSH鍵ペア生成と設定案内スクリプト

set -e

KEY_NAME="id_rsa_ai_co"
SSH_DIR="$HOME/.ssh"
KEY_PATH="$SSH_DIR/$KEY_NAME"

echo "GitHub Deploy Key 用のSSH鍵ペアを作成します。"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [ -f "$KEY_PATH" ] || [ -f "$KEY_PATH.pub" ]; then
  echo "既に鍵ファイルが存在します:"
  ls -l "$KEY_PATH"*
  read -p "上書きしますか？[y/N]: " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "処理を中止します。"
    exit 1
  fi
fi

ssh-keygen -t rsa -b 4096 -f "$KEY_PATH" -C "ai_co_deploy_key" -N ""

chmod 600 "$KEY_PATH"
chmod 644 "$KEY_PATH.pub"

echo "公開鍵の内容をGitHubの対象リポジトリの【Deploy keys】に追加してください。"
echo
echo "----- 公開鍵 -----"
cat "$KEY_PATH.pub"
echo "------------------"
echo

echo "追加手順の詳細はGitHubドキュメントをご覧ください。"
echo "https://docs.github.com/en/developers/overview/managing-deploy-keys"

echo
echo "SSH設定ファイルに以下を追記すると便利です:"
echo "Host github-ai-co"
echo "  HostName github.com"
echo "  User git"
echo "  IdentityFile $KEY_PATH"
echo "  IdentitiesOnly yes"
echo

echo "設定後は以下のコマンドでGitHubにSSH接続できるかテストしてください:"
echo "ssh -T git@github.com"

echo
echo "準備完了です！"

