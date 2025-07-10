-- pgvector Sample Queries for A2A Communication Analysis
-- Generated: 2025-07-10T02:50:57.512348

-- Find similar communications
-- 特定の通信に類似した通信を検索

                    -- 最新の通信から類似検索
                    WITH latest_comm AS (
                        SELECT embedding 
                        FROM a2a.communications 
                        WHERE embedding IS NOT NULL 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    )
                    SELECT * FROM a2a.find_similar_communications(
                        (SELECT embedding FROM latest_comm), 
                        10
                    );
                

-- Anomaly pattern search
-- 特定の異常パターンに類似したパターンを検索

                    -- 重要度の高い異常パターンの類似検索
                    SELECT 
                        a1.pattern_name,
                        a1.severity,
                        a1.occurrence_count,
                        1 - (a1.embedding <=> a2.embedding) as similarity
                    FROM a2a.anomaly_patterns a1
                    CROSS JOIN a2a.anomaly_patterns a2
                    WHERE a2.pattern_name = 'system-overload'
                      AND a1.pattern_name != a2.pattern_name
                      AND a1.embedding IS NOT NULL
                      AND a2.embedding IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT 5;
                

-- Agent communication patterns
-- エージェント間の通信パターン分析

                    -- エージェント別通信統計
                    SELECT 
                        sender,
                        receiver,
                        message_type,
                        COUNT(*) as message_count,
                        MAX(timestamp) as last_communication
                    FROM a2a.communications
                    GROUP BY sender, receiver, message_type
                    ORDER BY message_count DESC
                    LIMIT 20;
                

