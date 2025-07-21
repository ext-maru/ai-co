#!/usr/bin/env python3
"""
強化版テンプレートのクイックテスト
"""

import sys
from pathlib import Path
import asyncio

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from libs.code_generation.template_manager import CodeGenerationTemplateManager


async def test_enhanced_template():
    """強化版テンプレートのテスト"""
    print("🚀 Testing Enhanced Template System...")
    
    template_mgr = CodeGenerationTemplateManager()
    
    # テスト用Issue
    test_issue = {
        "number": 999,
        "title": "Build async REST API with JWT authentication",
        "body": """Requirements:
        - FastAPI framework with async endpoints
        - JWT token authentication
        - PostgreSQL database integration
        - CORS support for frontend
        - Comprehensive error handling
        - Performance optimization
        """
    }
    
    print(f"🔧 Issue: {test_issue['title']}")
    
    # Phase 3統合コンテキスト生成
    context = await template_mgr.create_context_from_issue(
        issue_number=test_issue["number"],
        issue_title=test_issue["title"],
        issue_body=test_issue["body"],
        use_advanced_analysis=True,
        use_pattern_learning=True
    )
    
    print(f"📊 Context generated with {len(context)} fields")
    print(f"Tech stack: {context.get('tech_stack', 'Unknown')}")
    
    # 強化版テンプレートでコード生成
    try:
        print(f"🔧 Attempting to use enhanced template for {context['tech_stack']}")
        
        # デバッグ: テンプレートパス確認
        template_path = f"{context['tech_stack']}/class_enhanced.j2"
        template_full_path = template_mgr.template_dir / template_path
        print(f"🔍 Template path: {template_full_path}")
        print(f"🔍 Template exists: {template_full_path.exists()}")
        
        enhanced_code = template_mgr.generate_code(
            template_type='class',
            tech_stack=context['tech_stack'],
            context=context,
            use_enhanced=True
        )
        
        print(f"✅ Enhanced template code generated ({len(enhanced_code)} chars)")
        
        # デバッグ: 生成コードの一部を表示
        print(f"🔍 Code sample (first 500 chars):")
        print(enhanced_code[:500])
        print("...")
        
        # 品質チェック（拡張版）
        quality_checks = {
            "Has async/await": "async def" in enhanced_code or "await " in enhanced_code,
            "Has specific exceptions": any(exc in enhanced_code for exc in ["ValueError", "TypeError", "ConnectionError", "TimeoutError"]),
            "Has structured logging": "extra=" in enhanced_code and "logger" in enhanced_code,
            "Has context managers": "async with" in enhanced_code or "with " in enhanced_code,
            "Has error chaining": " from e" in enhanced_code,
            "Has type hints": " -> " in enhanced_code and ": " in enhanced_code,
            "Has comprehensive docstrings": '"""' in enhanced_code and "Args:" in enhanced_code,
            "Has performance considerations": "timeout" in enhanced_code or "pool" in enhanced_code,
            "Has resource cleanup": "cleanup" in enhanced_code or "__aexit__" in enhanced_code,
            "Has proper imports": "import asyncio" in enhanced_code or "import aiohttp" in enhanced_code,
        }
        
        passed_checks = sum(quality_checks.values())
        total_checks = len(quality_checks)
        quality_score = (passed_checks / total_checks) * 100
        
        print(f"\n📈 Enhanced Quality Analysis:")
        for check, passed in quality_checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        print(f"\n🎯 Quality Score: {quality_score:.1f}/100")
        
        # 改善確認
        if quality_score >= 90:
            print("🎉 Target achieved! 90+ quality score!")
            return True
        else:
            print(f"📈 Improvement needed: {90 - quality_score:.1f} points to target")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced template failed: {e}")
        
        # フォールバック: 標準テンプレート
        try:
            standard_code = template_mgr.generate_code(
                template_type='class',
                tech_stack=context['tech_stack'],
                context=context,
                use_enhanced=False
            )
            print(f"🔄 Fallback to standard template ({len(standard_code)} chars)")
            return False
        except Exception as e2:
            print(f"❌ Standard template also failed: {e2}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_enhanced_template())
    print(f"\n{'✅ Enhanced template test PASSED!' if success else '⚠️ Enhanced template needs work, but functional.'}")