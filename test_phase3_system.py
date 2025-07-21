#!/usr/bin/env python3
"""
Phase 3 コードベース学習システムのテスト
Issue #184 Phase 3 完了確認用
"""

import sys
from pathlib import Path
import json
import asyncio

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from libs.code_generation.template_manager import CodeGenerationTemplateManager
from libs.code_generation.codebase_analyzer import CodebaseAnalyzer
from libs.code_generation.pattern_learning import PatternLearningEngine
from libs.code_generation.context_enhancer import ContextEnhancer


async def test_codebase_analyzer():
    """コードベース分析のテスト"""
    print("=== 1. Testing Codebase Analyzer ===\n")
    
    analyzer = CodebaseAnalyzer()
    
    # 小規模なテスト用分析
    result = await analyzer.analyze_codebase()
    
    print(f"📊 Codebase Analysis Results:")
    print(f"   - Total files analyzed: {result['total_files']}")
    print(f"   - Total lines: {result['basic_stats']['total_lines']}")
    print(f"   - Total functions: {result['basic_stats']['total_functions']}")
    print(f"   - Total classes: {result['basic_stats']['total_classes']}")
    print(f"   - Average file size: {result['basic_stats']['average_file_size']:.1f} lines")
    
    # パターン統計
    patterns = result.get("patterns", {})
    print(f"\n🔍 Pattern Analysis:")
    print(f"   - Import patterns found: {len(patterns.get('imports', []))}")
    print(f"   - Class definitions: {len(patterns.get('classes', []))}")
    print(f"   - Function definitions: {len(patterns.get('functions', []))}")
    print(f"   - Error handling patterns: {len(patterns.get('error_handling', []))}")
    
    # カテゴリ分析
    categorized = result.get("categorized_files", {})
    print(f"\n📁 File Categories:")
    for category, files in categorized.items():
        print(f"   - {category}: {len(files)} files")
    
    return result


async def test_pattern_learning():
    """パターン学習のテスト"""
    print("\n=== 2. Testing Pattern Learning Engine ===\n")
    
    engine = PatternLearningEngine()
    
    # コードベースから学習
    learning_result = await engine.learn_from_codebase()
    
    print(f"🧠 Pattern Learning Results:")
    patterns_learned = learning_result["patterns_learned"]
    for pattern_type, count in patterns_learned.items():
        print(f"   - {pattern_type}: {count}")
    
    print(f"\n📊 Learning Quality:")
    print(f"   - Confidence score: {learning_result['confidence_score']:.2f}")
    
    # 学習済みパターンの例を表示
    learned_patterns = engine.get_patterns_for_context()
    print(f"\n📋 Sample Learned Patterns:")
    print(f"   - Common imports: {len(learned_patterns['imports'])}")
    print(f"   - Style preferences: {learned_patterns['style_preferences']}")
    print(f"   - Naming conventions: {learned_patterns['naming']}")
    print(f"   - Project vocabulary: {learned_patterns['vocabulary'][:5]}")
    
    return learning_result, engine


async def test_context_enhancement():
    """コンテキスト強化のテスト"""
    print("\n=== 3. Testing Context Enhancement ===\n")
    
    # パターン学習エンジンを作成
    pattern_engine = PatternLearningEngine()
    enhancer = ContextEnhancer(pattern_engine)
    
    # テスト用コンテキスト
    test_context = {
        "issue_number": 300,
        "issue_title": "Implement async data processing pipeline",
        "issue_body": """Create an async data processing pipeline that can:
        - Read CSV files from multiple sources
        - Process data with pandas
        - Save results to database
        - Handle errors gracefully
        - Log processing status""",
        "tech_stack": "data",
        "complexity": "high"
    }
    
    print(f"🔧 Original Context:")
    print(f"   - Fields: {len(test_context)}")
    print(f"   - Issue: {test_context['issue_title']}")
    print(f"   - Tech stack: {test_context['tech_stack']}")
    
    # コンテキスト強化
    enhanced_context = await enhancer.enhance_context(test_context)
    
    print(f"\n✨ Enhanced Context:")
    print(f"   - Total fields: {len(enhanced_context)}")
    print(f"   - New fields added: {len(enhanced_context) - len(test_context)}")
    
    # 強化内容の詳細
    if "enhanced_imports" in enhanced_context:
        print(f"   - Enhanced imports: {len(enhanced_context['enhanced_imports'])}")
    
    if "quality_improvements" in enhanced_context:
        print(f"   - Quality improvements: {len(enhanced_context['quality_improvements'])}")
    
    if "similar_implementations" in enhanced_context:
        print(f"   - Similar implementations: {len(enhanced_context['similar_implementations'])}")
    
    if "project_context" in enhanced_context:
        project_ctx = enhanced_context["project_context"]
        print(f"   - Domain terms found: {len(project_ctx.get('domain_terms', []))}")
    
    return enhanced_context


async def test_integrated_template_system():
    """統合テンプレートシステムのテスト"""
    print("\n=== 4. Testing Integrated Template System ===\n")
    
    template_mgr = CodeGenerationTemplateManager()
    
    # 複雑なIssueでテスト
    complex_issue = {
        "number": 400,
        "title": "Build microservice for user authentication with JWT",
        "body": """Requirements:
        - FastAPI framework
        - JWT token generation
        - User registration and login
        - Password hashing with bcrypt
        - Database integration with SQLAlchemy
        - Async operations
        - Comprehensive error handling
        - Structured logging
        - Type hints for all functions
        - 95%+ test coverage"""
    }
    
    print(f"🔄 Testing Phase 3 Integration:")
    print(f"   - Issue: {complex_issue['title']}")
    
    # Phase 3統合コンテキスト生成
    context = await template_mgr.create_context_from_issue(
        issue_number=complex_issue["number"],
        issue_title=complex_issue["title"],
        issue_body=complex_issue["body"],
        use_advanced_analysis=True,
        use_pattern_learning=True
    )
    
    print(f"\n📊 Generated Context:")
    print(f"   - Total fields: {len(context)}")
    print(f"   - Tech stack detected: {context.get('tech_stack', 'Unknown')}")
    print(f"   - Complexity: {context.get('complexity', 'Unknown')}")
    
    # Phase 3特有のフィールドをチェック
    phase3_fields = [
        "enhanced_imports", "style_guide", "error_handling_guide",
        "logging_guide", "naming_guide", "project_context",
        "similar_implementations", "quality_improvements"
    ]
    
    phase3_count = sum(1 for field in phase3_fields if field in context)
    print(f"   - Phase 3 fields present: {phase3_count}/{len(phase3_fields)}")
    
    # コード生成テスト
    print(f"\n🔧 Testing Code Generation:")
    
    try:
        impl_code = template_mgr.generate_code(
            template_type='class',
            tech_stack=context['tech_stack'],
            context=context
        )
        
        test_code = template_mgr.generate_code(
            template_type='test',
            tech_stack=context['tech_stack'],
            context=context
        )
        
        # 品質チェック（Phase 3強化版）
        quality_score = 0
        enhanced_checks = {
            "No placeholder code": "return 'success'" not in impl_code and "pass" not in impl_code,
            "Has proper imports": "import" in impl_code,
            "Has class definition": "class" in impl_code,
            "Has async support": "async def" in impl_code,
            "Has error handling": "try:" in impl_code and "except" in impl_code,
            "Has logging": "logger" in impl_code or "logging" in impl_code,
            "Has type hints": "->" in impl_code and ":" in impl_code,
            "Has docstrings": '"""' in impl_code,
            "Test has assertions": "assert" in test_code,
            "Test has mocking": "mock" in test_code.lower(),
            # Phase 3新規チェック
            "Has specific exceptions": any(exc in impl_code for exc in ["ValueError", "FileNotFoundError", "HTTPError"]),
            "Has structured logging": "f'" in impl_code and "logger" in impl_code,
            "Has context manager": "with " in impl_code,
            "Has proper error chaining": "from " in impl_code and "except" in impl_code,
            "Has performance considerations": "async" in impl_code or "await" in impl_code
        }
        
        print(f"\n✅ Enhanced Quality Checks:")
        for check, passed in enhanced_checks.items():
            status = "✓" if passed else "✗"
            print(f"   {status} {check}")
            if passed:
                quality_score += 100 / len(enhanced_checks)
        
        print(f"\n📈 Quality Score: {quality_score:.1f}/100")
        
        return {
            "context_fields": len(context),
            "phase3_fields": phase3_count,
            "quality_score": quality_score,
            "success": quality_score >= 95
        }
        
    except Exception as e:
        print(f"❌ Code generation failed: {e}")
        return {"success": False, "error": str(e)}


async def test_performance():
    """パフォーマンステスト"""
    print("\n=== 5. Testing Performance ===\n")
    
    import time
    
    # 初期化時間
    start_time = time.time()
    template_mgr = CodeGenerationTemplateManager()
    init_time = time.time() - start_time
    
    # コンテキスト生成時間
    start_time = time.time()
    context = await template_mgr.create_context_from_issue(
        issue_number=500,
        issue_title="Performance test issue",
        issue_body="Test the performance of the Phase 3 system",
        use_pattern_learning=True
    )
    context_time = time.time() - start_time
    
    # コード生成時間
    start_time = time.time()
    code = template_mgr.generate_code(
        template_type='class',
        tech_stack=context['tech_stack'],
        context=context
    )
    generation_time = time.time() - start_time
    
    print(f"⚡ Performance Results:")
    print(f"   - Initialization: {init_time:.3f}s")
    print(f"   - Context generation: {context_time:.3f}s")
    print(f"   - Code generation: {generation_time:.3f}s")
    print(f"   - Total time: {init_time + context_time + generation_time:.3f}s")
    
    # パフォーマンス基準
    total_time = init_time + context_time + generation_time
    performance_ok = total_time < 10.0  # 10秒以内
    
    print(f"   - Performance: {'✓ PASS' if performance_ok else '✗ SLOW'}")
    
    return {
        "init_time": init_time,
        "context_time": context_time,
        "generation_time": generation_time,
        "total_time": total_time,
        "performance_ok": performance_ok
    }


async def main():
    """メイン関数"""
    print("🔬 Testing Phase 3: Codebase Learning System")
    print("=" * 60)
    
    try:
        # 1. コードベース分析テスト
        codebase_result = await test_codebase_analyzer()
        
        # 2. パターン学習テスト
        learning_result, pattern_engine = await test_pattern_learning()
        
        # 3. コンテキスト強化テスト
        enhanced_context = await test_context_enhancement()
        
        # 4. 統合システムテスト
        integration_result = await test_integrated_template_system()
        
        # 5. パフォーマンステスト
        performance_result = await test_performance()
        
        # 最終評価
        print("\n\n=== Phase 3 Final Assessment ===")
        
        success_criteria = {
            "Codebase analysis": codebase_result["total_files"] > 0,
            "Pattern learning": learning_result["confidence_score"] > 0.5,
            "Context enhancement": len(enhanced_context) > 10,
            "Integration": integration_result.get("success", False),
            "Performance": performance_result["performance_ok"]
        }
        
        passed_tests = sum(success_criteria.values())
        total_tests = len(success_criteria)
        
        print(f"\n📊 Test Results:")
        for test_name, passed in success_criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   - {test_name}: {status}")
        
        print(f"\n🎯 Overall Score: {passed_tests}/{total_tests} tests passed")
        
        if integration_result.get("quality_score"):
            print(f"🏆 Code Quality Score: {integration_result['quality_score']:.1f}/100")
        
        # Phase 3完了判定
        phase3_success = (
            passed_tests >= 4 and 
            integration_result.get("quality_score", 0) >= 95
        )
        
        print(f"\n{'✅ Phase 3 COMPLETED!' if phase3_success else '❌ Phase 3 needs improvement'}")
        
        if phase3_success:
            print("📈 Expected improvement: +5-10 points (Total: 100-105/100)")
            print("🎉 Issue #184 ready for completion!")
        
        return phase3_success
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)