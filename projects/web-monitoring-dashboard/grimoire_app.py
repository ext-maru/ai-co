#!/usr/bin/env python3
"""
Magic Grimoire Web Application
魔法書WebUIアプリケーション - Flask + React API
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

from libs.grimoire_database import GrimoireDatabase, SpellType, MagicSchool, EvolutionType
from libs.grimoire_vector_search import GrimoireVectorSearch, SearchQuery, SearchResult
from libs.grimoire_spell_evolution import EvolutionEngine, EvolutionStrategy

logger = logging.getLogger(__name__)

class GrimoireWebApp:
    """魔法書Webアプリケーション"""
    
    def __init__(self):
        """初期化"""
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        self.app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'grimoire-secret-key')
        
        # CORS設定
        CORS(self.app, resources={
            r"/api/*": {
                "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
        
        # システム初期化
        self.database = GrimoireDatabase()
        self.search_engine = GrimoireVectorSearch(database=self.database)
        self.evolution_engine = EvolutionEngine(database=self.database)
        
        # ルート設定
        self._setup_routes()
        
        logger.info("🌐 Grimoire Web Application initialized")
    
    async def initialize(self) -> bool:
        """システム初期化"""
        try:
            await self.database.initialize()
            await self.search_engine.initialize()
            await self.evolution_engine.initialize()
            
            logger.info("✅ Grimoire Web App ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Web app initialization failed: {e}")
            return False
    
    def _setup_routes(self):
        """ルート設定"""
        
        # ===============================
        # メインページ
        # ===============================
        
        @self.app.route('/')
        def index():
            """メインページ"""
            return render_template('index.html')
        
        @self.app.route('/library')
        def library():
            """魔法書図書館"""
            return render_template('library.html')
        
        @self.app.route('/search')
        def search_page():
            """検索ページ"""
            return render_template('search.html')
        
        @self.app.route('/evolution')
        def evolution():
            """昇華管理ページ"""
            return render_template('evolution.html')
        
        @self.app.route('/admin')
        def admin():
            """グランドエルダー管理ページ"""
            return render_template('admin.html')
        
        # ===============================
        # API エンドポイント
        # ===============================
        
        # 検索API
        @self.app.route('/api/search', methods=['POST'])
        def api_search():
            """セマンティック検索API"""
            try:
                data = request.get_json()
                if not data or 'query' not in data:
                    raise BadRequest("Query text is required")
                
                # 検索実行
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                search_query = SearchQuery(
                    query_text=data['query'],
                    limit=data.get('limit', 10),
                    similarity_threshold=data.get('threshold', 0.7),
                    include_eternal_only=data.get('eternal_only', False),
                    magic_schools=[MagicSchool(school) for school in data.get('schools', [])] if data.get('schools') else None,
                    spell_types=[SpellType(stype) for stype in data.get('types', [])] if data.get('types') else None,
                    min_power_level=data.get('min_power', None)
                )
                
                results = loop.run_until_complete(self.search_engine.search(search_query))
                loop.close()
                
                # 結果をJSON形式に変換
                search_results = []
                for result in results:
                    search_results.append({
                        'spell_id': result.spell_id,
                        'spell_name': result.spell_name,
                        'content': result.content,
                        'similarity_score': result.similarity_score,
                        'spell_type': result.spell_type,
                        'magic_school': result.magic_school,
                        'tags': result.tags,
                        'power_level': result.power_level,
                        'is_eternal': result.is_eternal,
                        'casting_frequency': result.casting_frequency,
                        'created_at': result.created_at.isoformat() if result.created_at else None,
                        'snippet': result.snippet
                    })
                
                return jsonify({
                    'success': True,
                    'results': search_results,
                    'total': len(search_results),
                    'query': data['query']
                })
                
            except Exception as e:
                logger.error(f"Search API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # 呪文詳細API
        @self.app.route('/api/spells/<spell_id>', methods=['GET'])
        def api_get_spell(spell_id):
            """呪文詳細取得API"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                spell_data = loop.run_until_complete(self.database.get_spell_by_id(spell_id))
                
                if not spell_data:
                    raise NotFound(f"Spell not found: {spell_id}")
                
                # 関連呪文取得
                related_spells = loop.run_until_complete(
                    self.search_engine.find_related_spells(spell_id, limit=5)
                )
                
                # 昇華履歴取得
                evolution_history = loop.run_until_complete(
                    self.database.get_evolution_history(spell_id)
                )
                
                loop.close()
                
                # レスポンス作成
                response_data = {
                    'spell': {
                        'id': spell_data['id'],
                        'spell_name': spell_data['spell_name'],
                        'content': spell_data['content'],
                        'spell_type': spell_data['spell_type'],
                        'magic_school': spell_data['magic_school'],
                        'tags': spell_data['tags'],
                        'power_level': spell_data['power_level'],
                        'casting_frequency': spell_data['casting_frequency'],
                        'is_eternal': spell_data['is_eternal'],
                        'created_at': spell_data['created_at'].isoformat() if spell_data.get('created_at') else None,
                        'updated_at': spell_data['updated_at'].isoformat() if spell_data.get('updated_at') else None,
                        'version': spell_data.get('version', 1)
                    },
                    'related_spells': [
                        {
                            'spell_id': r.spell_id,
                            'spell_name': r.spell_name,
                            'similarity_score': r.similarity_score,
                            'snippet': r.snippet
                        } for r in related_spells
                    ],
                    'evolution_history': [
                        {
                            'id': h['id'],
                            'evolution_type': h['evolution_type'],
                            'evolution_reason': h['evolution_reason'],
                            'evolved_at': h['evolved_at'].isoformat() if h.get('evolved_at') else None,
                            'original_name': h.get('original_name'),
                            'evolved_name': h.get('evolved_name')
                        } for h in evolution_history
                    ]
                }
                
                return jsonify({'success': True, 'data': response_data})
                
            except NotFound as e:
                return jsonify({'success': False, 'error': str(e)}), 404
            except Exception as e:
                logger.error(f"Get spell API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # 呪文作成API
        @self.app.route('/api/spells', methods=['POST'])
        def api_create_spell():
            """呪文作成API"""
            try:
                data = request.get_json()
                if not data:
                    raise BadRequest("Spell data is required")
                
                required_fields = ['spell_name', 'content']
                for field in required_fields:
                    if field not in data:
                        raise BadRequest(f"Required field missing: {field}")
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 自動タグ提案
                suggested_tags = loop.run_until_complete(
                    self.search_engine.suggest_tags(data['content'])
                )
                
                spell_data = {
                    'spell_name': data['spell_name'],
                    'content': data['content'],
                    'spell_type': data.get('spell_type', SpellType.KNOWLEDGE.value),
                    'magic_school': data.get('magic_school', MagicSchool.KNOWLEDGE_SAGE.value),
                    'tags': data.get('tags', suggested_tags),
                    'power_level': data.get('power_level', 1),
                    'is_eternal': data.get('is_eternal', False)
                }
                
                # 呪文作成とインデックス化
                spell_id = loop.run_until_complete(
                    self.search_engine.index_spell(str(uuid.uuid4()), spell_data)
                )
                
                loop.close()
                
                return jsonify({
                    'success': True,
                    'spell_id': spell_id,
                    'suggested_tags': suggested_tags
                })
                
            except BadRequest as e:
                return jsonify({'success': False, 'error': str(e)}), 400
            except Exception as e:
                logger.error(f"Create spell API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # 昇華計画API
        @self.app.route('/api/evolution/plan', methods=['POST'])
        def api_create_evolution_plan():
            """昇華計画作成API"""
            try:
                data = request.get_json()
                if not data or 'spell_ids' not in data:
                    raise BadRequest("Spell IDs are required")
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                evolution_type = EvolutionType(data['evolution_type']) if data.get('evolution_type') else None
                strategy = EvolutionStrategy(data.get('strategy', EvolutionStrategy.INTELLIGENT.value))
                
                plan = loop.run_until_complete(
                    self.evolution_engine.create_evolution_plan(
                        data['spell_ids'],
                        evolution_type,
                        strategy
                    )
                )
                
                loop.close()
                
                return jsonify({
                    'success': True,
                    'plan': {
                        'plan_id': plan.plan_id,
                        'evolution_type': plan.evolution_type.value,
                        'strategy': plan.strategy.value,
                        'original_spell_ids': plan.original_spell_ids,
                        'target_spell_data': plan.target_spell_data,
                        'confidence_score': plan.confidence_score,
                        'reasoning': plan.reasoning,
                        'estimated_impact': plan.estimated_impact,
                        'created_at': plan.created_at.isoformat()
                    }
                })
                
            except BadRequest as e:
                return jsonify({'success': False, 'error': str(e)}), 400
            except Exception as e:
                logger.error(f"Evolution plan API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # 昇華実行API
        @self.app.route('/api/evolution/execute', methods=['POST'])
        def api_execute_evolution():
            """昇華実行API"""
            try:
                data = request.get_json()
                if not data or 'plan_id' not in data:
                    raise BadRequest("Plan ID is required")
                
                # 実装簡略化：セッション管理なしの場合
                return jsonify({
                    'success': False,
                    'error': 'Evolution execution requires session management - not implemented in this demo'
                }), 501
                
            except BadRequest as e:
                return jsonify({'success': False, 'error': str(e)}), 400
            except Exception as e:
                logger.error(f"Evolution execute API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # 統計API
        @self.app.route('/api/stats', methods=['GET'])
        def api_get_stats():
            """統計情報取得API"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                stats = loop.run_until_complete(self.search_engine.get_search_statistics())
                loop.close()
                
                return jsonify({
                    'success': True,
                    'stats': stats
                })
                
            except Exception as e:
                logger.error(f"Stats API error: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # ヘルスチェック
        @self.app.route('/api/health', methods=['GET'])
        def api_health():
            """ヘルスチェックAPI"""
            return jsonify({
                'success': True,
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'version': '1.0.0'
            })
        
        # エラーハンドラー
        @self.app.errorhandler(404)
        def not_found(error):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Not found'}), 404
            return render_template('404.html'), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Internal server error'}), 500
            return render_template('500.html'), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """アプリケーション実行"""
        logger.info(f"🌐 Starting Grimoire Web App on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

# Flask アプリケーションインスタンス（WSGI用）
grimoire_app = GrimoireWebApp()
app = grimoire_app.app

# 開発用実行
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Magic Grimoire Web Application")
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    # ログ設定
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    
    # 初期化
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        if not loop.run_until_complete(grimoire_app.initialize()):
            logger.error("Failed to initialize application")
            sys.exit(1)
        
        grimoire_app.run(host=args.host, port=args.port, debug=args.debug)
        
    finally:
        loop.close()