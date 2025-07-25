#!/usr/bin/env python3
"""
RAG賢者修正のテスト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# インポートテスト
try:
    from libs.rag_manager import RagManager
    print("✅ RAG Manager imported successfully")
    
    from libs.knowledge_sage import KnowledgeSage
    print("✅ Knowledge Sage imported successfully")
    
    from libs.task_sage import TaskSage
    print("✅ Task Sage imported successfully")
    
    from libs.incident_sage import IncidentSage
    print("✅ Incident Sage imported successfully")
    
    from libs.elder_system.flow.elder_flow_engine import ElderFlowEngine
    print("✅ Elder Flow Engine imported successfully")
    
    from libs.integrations.github.api_implementations.create_pull_request import GitHubCreatePullRequestImplementation
    print("✅ GitHub PR Creator imported successfully")
    
    # AutoIssueProcessorのインポート
    from libs.integrations.github.auto_issue_processor import AutoIssueProcessor
    print("✅ AutoIssueProcessor imported successfully")
    
    print("\n✅ All imports successful! RAG issue fixed.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)