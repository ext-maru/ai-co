# AI Company SSH Keys Backup

## 🔑 SSH鍵永続化バックアップ

このディレクトリにはAI CompanyプロジェクトのGitHub認証用SSH鍵のバックアップが保存されています。

### 含まれるファイル
- `id_rsa` / `id_rsa.pub` - RSA 4096bit鍵ペア
- `id_ed25519` / `id_ed25519.pub` - ED25519鍵ペア

### 復元方法
```bash
# SSH鍵が失われた場合の復元手順
cp /home/aicompany/ai_co/.ssh_backup/id_rsa* ~/.ssh/
cp /home/aicompany/ai_co/.ssh_backup/id_ed25519* ~/.ssh/
chmod 600 ~/.ssh/id_rsa ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_rsa.pub ~/.ssh/id_ed25519.pub

# SSH agent に追加
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
ssh-add ~/.ssh/id_ed25519

# 接続テスト
ssh -T git@github.com
```

### GitHub設定済み公開鍵
**RSA公開鍵（推奨）:**
```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCSnI36LBuHGcO2wii39kFkSDzxNb4jmuEvU6noEFhMahgiEfbbEjrrnAqes4vPzAi4ZWzXexOmH3zlTtV7C9eDYhw9Oa+tPASK+nRx0jCNBKMQBskwwyIuXfYJ5qSLBPsI6F8kn28MgASsi3e08OxcNKm9QJ+Igh3nsMw9BqyeoIHxWCDJzYuquGbF/6D/Rl1nQ0zwCIwcsu/SWrIZxQUhZH6ephNx4mJzoM8wZVbz+GTzlcyrpziMt/tc72KzZl7AEhhQMABIy7Y3//ZHXnFDrK08IjmCGCe60wSzjX7x0evcyUlYAtgyMl/oQbu1jDLnhTaxx21Tr2i4jc/pPM4tiH526eVd7unUqx7bpz38bGwWBT+wV1R7XwnRoZF5Hutp6GvB6T4eovskvrksu0tSvoG5MTMn7GxfQxnqehy7e16nQc5pXh/4+ynysGCRYDmaALBVJRXRA836BDMKp0nxD5z7zyVROVaCVsb7yEMYyikkHQCUgFqMjAZVouxX0hT3fclhGQURbRtnv0+O0rI3+vvIunIw9nwAQmOiBa2E6eoCNdDECv1zT7T+fJ34uk3u3XXzOhKdKWcYEE3H2+kTyDIk2kqSnVGF4+6KjA3lMk717ZwYCZyakw4agUmc2S1eNsnGNkFq40GV1TUhc74CRNPmNQbBABatJta/UoLoGw== aicompany@ai-co
```

**作成日:** 2025年7月6日
**用途:** GitHub ext-maru/ai-co リポジトリアクセス

⚠️ **重要:** これらの鍵は機密情報です。安全に管理してください。