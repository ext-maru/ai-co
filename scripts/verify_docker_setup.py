#!/usr/bin/env python3
"""
Dockerの起動可能性とプロジェクトの検証
"""

import json
import os
import subprocess
from pathlib import Path


def check_docker_installation():
    """Dockerがインストールされているか確認"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, "Docker is not installed"
    except FileNotFoundError:
        return False, "Docker command not found"


def check_docker_compose_installation():
    """Docker Composeがインストールされているか確認"""
    try:
        # 新しいバージョン (docker compose)
        result = subprocess.run(
            ["docker", "compose", "version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            return True, f"Docker Compose (plugin): {result.stdout.strip()}"

        # 古いバージョン (docker-compose)
        result = subprocess.run(
            ["docker-compose", "--version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            return True, f"Docker Compose (standalone): {result.stdout.strip()}"

        return False, "Docker Compose is not installed"
    except FileNotFoundError:
        return False, "Docker Compose command not found"


def verify_project_structure():
    """プロジェクト構造を検証"""
    project_path = Path("/home/aicompany/ai_co/projects/image-upload-manager")

    required_files = [
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
        "app/app.py",
        "README.md",
    ]

    missing_files = []
    for file in required_files:
        if not (project_path / file).exists():
            missing_files.append(file)

    return len(missing_files) == 0, missing_files


def check_port_availability(port=5000):
    """ポートが利用可能か確認"""
    try:
        result = subprocess.run(["ss", "-tln"], capture_output=True, text=True)
        if f":{port}" in result.stdout:
            return False, f"Port {port} is already in use"
        return True, f"Port {port} is available"
    except:
        return None, "Could not check port availability"


def main():
    """mainメソッド"""
    print("🐳 Docker環境検証レポート")
    print("=" * 60)

    # Dockerインストール確認
    docker_ok, docker_msg = check_docker_installation()
    print(f"📦 Docker: {'✅' if docker_ok else '❌'} {docker_msg}")

    # Docker Composeインストール確認
    compose_ok, compose_msg = check_docker_compose_installation()
    print(f"📦 Docker Compose: {'✅' if compose_ok else '❌'} {compose_msg}")

    # プロジェクト構造検証
    print("\n📂 プロジェクト構造検証")
    print("-" * 40)
    structure_ok, missing = verify_project_structure()
    if structure_ok:
        print("✅ すべての必須ファイルが存在します")
    else:
        print("❌ 以下のファイルが不足しています:")
        for file in missing:
            print(f"   - {file}")

    # ポート確認
    print("\n🔌 ポート可用性")
    print("-" * 40)
    port_ok, port_msg = check_port_availability(5000)
    if port_ok is not None:
        print(f"{'✅' if port_ok else '⚠️'} {port_msg}")
    else:
        print(f"❓ {port_msg}")

    # プロジェクト登録確認
    print("\n📋 プロジェクト登録状況")
    print("-" * 40)
    index_file = Path("/home/aicompany/ai_co/data/project_index.json")
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            projects = json.load(f)
            if "image-upload-manager" in projects:
                project = projects["image-upload-manager"]
                print("✅ プロジェクトが正常に登録されています")
                print(f"   名前: {project['name']}")
                print(f"   ステータス: {project['status']}")
                print(f"   進捗: {project['progress']*100:0.0f}%")
                print(f"   タグ: {', '.join(project['tags'])}")
            else:
                print("❌ プロジェクトが登録されていません")
    else:
        print("❌ プロジェクトインデックスファイルが存在しません")

    # 起動手順
    print("\n🚀 Dockerコンテナ起動手順")
    print("-" * 40)
    if docker_ok and compose_ok:
        print("以下のコマンドでDockerコンテナを起動できます:")
        print("\n  cd /home/aicompany/ai_co/projects/image-upload-manager")
        print("  docker compose up -d")
        print("\nコンテナのログを確認:")
        print("  docker compose logs -f")
        print("\nコンテナを停止:")
        print("  docker compose down")
    else:
        print("⚠️ DockerまたはDocker Composeがインストールされていません")
        print("\n必要なソフトウェアをインストールしてください:")
        if not docker_ok:
            print("  - Docker: https://docs.docker.com/engine/install/")
        if not compose_ok:
            print("  - Docker Compose: https://docs.docker.com/compose/install/")


if __name__ == "__main__":
    main()
