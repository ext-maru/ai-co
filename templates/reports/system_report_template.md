# {{title}}

{{generated_at}}

## エグゼクティブサマリー

{{executive_summary}}

## 📊 システム概要

### 主要メトリクス
- **総タスク数**: {{total_tasks}}
- **完了タスク数**: {{completed_tasks}} ({{completion_rate}}%)
- **アクティブワーカー**: {{active_workers}}
- **システム稼働時間**: {{system_uptime}}

### キューステータス
- 保留中: {{queue_status.pending}}
- 処理中: {{queue_status.processing}}

## 🧙‍♂️ 4賢者システムステータス

{% for sage_name, sage_data in sage_analytics.items() %}
### {{sage_display_names[sage_name]}}
- **状態**: {{sage_data.status}}
{% if sage_name == 'knowledge_sage' %}
- **保存パターン数**: {{sage_data.stored_patterns}}
- **最近の学習**: {{sage_data.recent_learnings}}件
{% elif sage_name == 'task_sage' %}
- **管理タスク数**: {{sage_data.managed_tasks}}
- **最適化率**: {{sage_data.optimization_rate}}%
{% elif sage_name == 'incident_sage' %}
- **防止インシデント**: {{sage_data.prevented_incidents}}件
- **復旧成功率**: {{sage_data.recovery_success_rate}}%
{% elif sage_name == 'rag_sage' %}
- **検索精度**: {{sage_data.search_accuracy}}%
- **コンテキスト強化**: {{sage_data.context_enhancements}}件
{% endif %}
{% endfor %}

## 📈 パフォーマンス指標

### 応答性能
- **平均応答時間**: {{average_response_time}}秒
- **タスク完了率**: {{task_completion_rate}}%
- **システム可用性**: {{system_availability}}%

### リソース使用状況
- **CPU**: {{resource_utilization.cpu}}%
- **メモリ**: {{resource_utilization.memory}}%
- **ディスク**: {{resource_utilization.disk}}%

## 🚨 インシデント分析

### サマリー
- **総インシデント数**: {{incident_data.total_incidents}}
- **解決済み**: {{incident_data.resolved_incidents}}
- **平均解決時間**: {{incident_data.average_resolution_time}}分

### タイプ別分析
{% for incident_type, count in incident_data.incident_types.items() %}
- {{incident_type}}: {{count}}件
{% endfor %}

## 🎓 学習・進化状況

- **学習セッション**: {{learning_data.total_learning_sessions}}回
- **成功したコンセンサス**: {{learning_data.successful_consensus}}回
- **賢者間知識転送**: {{learning_data.cross_sage_transfers}}回
- **知識成長率**: {{learning_data.knowledge_growth_rate}}%

## 🎯 推奨アクション

{% for recommendation in recommendations %}
1. {{recommendation}}
{% endfor %}

## 📅 次回レポート予定

{{next_report_date}}

---
*このレポートはElders Guild 4賢者システムによって自動生成されました*