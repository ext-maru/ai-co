-- エルダーズギルド PostgreSQL データベースセットアップ
-- CorePostgres計画 Phase 0

-- データベース作成（postgres ユーザーで実行）
CREATE DATABASE elders_knowledge;

-- ユーザー作成と権限付与
CREATE USER elders_guild WITH PASSWORD 'elders_2025';
GRANT ALL PRIVILEGES ON DATABASE elders_knowledge TO elders_guild;

-- データベースに接続
\c elders_knowledge;

-- 拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- スキーマ作成
CREATE SCHEMA IF NOT EXISTS elders_guild;
CREATE SCHEMA IF NOT EXISTS knowledge_base;
CREATE SCHEMA IF NOT EXISTS task_management;
CREATE SCHEMA IF NOT EXISTS incident_tracking;
CREATE SCHEMA IF NOT EXISTS rag_system;

-- スキーマの権限設定
GRANT ALL ON SCHEMA elders_guild TO elders_guild;
GRANT ALL ON SCHEMA knowledge_base TO elders_guild;
GRANT ALL ON SCHEMA task_management TO elders_guild;
GRANT ALL ON SCHEMA incident_tracking TO elders_guild;
GRANT ALL ON SCHEMA rag_system TO elders_guild;

-- デフォルト権限の設定
ALTER DEFAULT PRIVILEGES IN SCHEMA elders_guild GRANT ALL ON TABLES TO elders_guild;
ALTER DEFAULT PRIVILEGES IN SCHEMA knowledge_base GRANT ALL ON TABLES TO elders_guild;
ALTER DEFAULT PRIVILEGES IN SCHEMA task_management GRANT ALL ON TABLES TO elders_guild;
ALTER DEFAULT PRIVILEGES IN SCHEMA incident_tracking GRANT ALL ON TABLES TO elders_guild;
ALTER DEFAULT PRIVILEGES IN SCHEMA rag_system GRANT ALL ON TABLES TO elders_guild;
