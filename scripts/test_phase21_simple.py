#!/usr/bin/env python3
"""
Phase 21実装のシンプルなテストスクリプト
TrackingDataIntegratorの動作確認
"""

import asyncio
import sys
import os
from datetime import datetime

# パスの追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.four_sages.knowledge.tracking_data_integrator import TrackingDataIntegrator
from libs.four_sages.knowledge.enhanced_knowledge_sage import EnhancedKnowledgeSage

async def test_tracking_data_integrator():
    """TrackingDataIntegratorの基本テスト"""
    print("🔍 TrackingDataIntegrator動作確認開始")
    
    try:
        # TrackingDataIntegratorのインスタンス化
        integrator = TrackingDataIntegrator()
        print("✅ TrackingDataIntegrator初期化成功")
        
        # 実行データの取得テスト
        print("\n📊 実行データ取得テスト")
        execution_data = await integrator.get_execution_data(days=7)
        print(f"  取得データ数: {len(execution_data)}")
        
        if execution_data:
            # パターン分析テスト
            print("\n🔮 パターン分析テスト")
            patterns = await integrator.analyze_execution_patterns(execution_data)
            print(f"  抽出パターン数: {len(patterns)}")
            
            for pattern in patterns[:3]:  # 最初の3パターンを表示
                print(f"  - {pattern.pattern_type}: {pattern.pattern_name " \
                    "if hasattr(pattern, 'pattern_name') else 'Pattern'} (信頼度: {pattern.confidence:.2f})")
            
            # メトリクス抽出テスト
            print("\n📏 メトリクス抽出テスト")
            metrics = await integrator.extract_execution_metrics(execution_data)
            print(f"  抽出メトリクス数: {len(metrics)}")
            
            if metrics:
                valid_scores = [m.quality_score for m in metrics if m.quality_score is not None]
                if valid_scores:
                    avg_quality = sum(valid_scores) / len(valid_scores)
                    print(f"  平均品質スコア: {avg_quality:.2f}")
                else:
                    print("  平均品質スコア: データなし")
        
        # 品質洞察の取得
        print("\n💡 品質洞察取得テスト")
        insights = await integrator.get_quality_insights(days=30)
        if insights:
            print(f"  分析期間: {insights.get('analysis_period_days')}日")
            print(f"  データポイント数: {insights.get('data_points')}")
            if 'recommendations' in insights:
                print(f"  推奨事項数: {len(insights['recommendations'])}")
        
        print("\n✅ TrackingDataIntegrator動作確認完了")
        return True
        
    except Exception as e:
        print(f"\n❌ エラー発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_knowledge_sage():
    """EnhancedKnowledgeSageの統合テスト"""
    print("\n\n🧙 EnhancedKnowledgeSage統合テスト開始")
    
    try:
        # EnhancedKnowledgeSageのインスタンス化
        sage = EnhancedKnowledgeSage()
        print("✅ EnhancedKnowledgeSage初期化成功")
        
        # ヘルスチェック
        print("\n🏥 ヘルスチェック")
        health_result = await sage.process_request({
            "type": "health_check"
        })
        print(f"  ステータス: {health_result.get('status', 'unknown')}")
        
        # パターン抽出リクエスト
        print("\n🎯 パターン抽出リクエスト")
        pattern_result = await sage.process_request({
            "type": "extract_patterns",
            "days": 7,
            "pattern_types": ["success", "failure"]
        })
        
        if pattern_result.get("success"):
            print(f"  ✅ パターン抽出成功: {pattern_result.get('patterns_extracted')}個")
        else:
            print(f"  ❌ パターン抽出失敗: {pattern_result.get('error')}")
        
        # 実行予測リクエスト
        print("\n🔮 実行予測リクエスト")
        prediction_result = await sage.process_request({
            "type": "predict_execution",
            "task_description": "Knowledge Sage統合テスト",
            "prediction_types": ["success", "time", "quality"]
        })
        
        if prediction_result.get("success"):
            print("  ✅ 予測成功")
            predictions = prediction_result.get("predictions", {})
            if "success_probability" in predictions:
                print(f"  成功確率: {predictions['success_probability']:.1%}")
        else:
            print(f"  ❌ 予測失敗: {prediction_result.get('error')}")
        
        print("\n✅ EnhancedKnowledgeSage統合テスト完了")
        return True
        
    except Exception as e:
        print(f"\n❌ エラー発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """メイン実行関数"""
    print("🌊 Phase 21: Knowledge Sage統合システムテスト")
    print("=" * 60)
    
    # TrackingDataIntegratorテスト
    integrator_success = await test_tracking_data_integrator()
    
    # EnhancedKnowledgeSageテスト
    sage_success = await test_enhanced_knowledge_sage()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    print(f"TrackingDataIntegrator: {'✅ 成功' if integrator_success else '❌ 失敗'}")
    print(f"EnhancedKnowledgeSage: {'✅ 成功' if sage_success else '❌ 失敗'}")
    
    overall_success = integrator_success and sage_success
    print(f"\n総合結果: {'✅ 全テスト成功' if overall_success else '❌ 一部テスト失敗'}")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)