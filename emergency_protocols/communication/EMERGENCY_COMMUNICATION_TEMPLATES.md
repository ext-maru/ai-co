# 📢 緊急時コミュニケーションテンプレート集

**文書番号**: ECT-001  
**最終更新**: 2025年7月10日  
**使用権限**: 緊急対応チーム  
**言語**: 日本語/英語

---

## 🔴 Disaster Level (災害級) テンプレート

### 内部通知 - 即時配信

```markdown
【最重要】AI Company 災害級インシデント発生

発生時刻: {{incident_timestamp}}
インシデントID: {{incident_id}}
影響レベル: DISASTER

【現在の状況】
{{incident_description}}

【影響範囲】
- 影響サービス: {{affected_services}}
- 影響ユーザー数: {{affected_users}}
- データリスク: {{data_risk_level}}

【緊急対応状況】
- Elder Council: 招集済み
- Grand Elder maru: 通知済み
- 自動対応: 実行中

【必要なアクション】
1. 指定の緊急会議に即座に参加
2. 担当システムの状態確認
3. 5分以内に状況報告

緊急会議URL: {{emergency_meeting_url}}
対策本部Slack: {{crisis_channel}}
```

### 外部通知 - お客様向け（初報）

```markdown
件名: 【重要】AI Companyサービス一時停止のお知らせ

お客様各位

平素よりAI Companyをご利用いただき、誠にありがとうございます。

{{incident_timestamp}}より、システムに重大な障害が発生し、
現在サービスの提供を一時的に停止しております。

【影響を受けるサービス】
{{affected_services_list}}

【現在の対応状況】
技術チーム総動員で復旧作業を行っております。
最優先で原因究明と復旧に取り組んでおります。

【復旧見込み】
{{estimated_recovery_time}}

最新の情報は以下でご確認いただけます：
状況確認ページ: {{status_page_url}}

ご利用のお客様には多大なるご迷惑をおかけしておりますこと、
深くお詫び申し上げます。

AI Company
緊急対策本部
```

### ステークホルダー向け

```markdown
件名: [URGENT] AI Company Critical System Incident

Dear Stakeholders,

We are experiencing a critical system incident affecting our core services.

Incident Details:
- Time: {{incident_timestamp}}
- Severity: DISASTER LEVEL
- Impact: {{business_impact}}

Current Actions:
- Emergency response team activated
- Grand Elder approval obtained
- Recovery procedures initiated

Business Continuity:
- Data integrity: {{data_status}}
- Estimated downtime: {{downtime_estimate}}
- Financial impact: {{financial_impact_estimate}}

We will provide updates every 30 minutes.

Next update: {{next_update_time}}

Contact:
Emergency Hotline: {{emergency_contact}}
Incident Commander: {{incident_commander}}
```

---

## 🟠 Critical Level (重大) テンプレート

### 内部通知

```markdown
【重要】Critical Level インシデント発生

インシデント概要:
- 発生時刻: {{timestamp}}
- 影響サービス: {{services}}
- 現在のステータス: {{status}}

対応チーム:
- インシデントコマンダー: {{commander}}
- 技術リード: {{tech_lead}}
- Elder Council: {{council_status}}

必要なアクション:
- {{team_member_1}}: {{action_1}}
- {{team_member_2}}: {{action_2}}
- {{team_member_3}}: {{action_3}}

進捗報告: 15分ごと
Slackチャンネル: {{incident_channel}}
```

### 外部通知（限定的影響）

```markdown
件名: AI Company一部機能の不具合について

お客様各位

現在、以下の機能において不具合が発生しております：

【影響を受ける機能】
{{affected_features}}

【影響時間帯】
{{start_time}} から継続中

【代替手段】
{{workaround_instructions}}

【復旧作業】
現在、復旧作業を実施中です。
{{recovery_eta}}までの復旧を見込んでおります。

ご不便をおかけし申し訳ございません。
```

---

## 🟡 Major Level (主要) テンプレート

### 内部通知

```markdown
【注意】Major Level インシデント

概要: {{brief_description}}
優先度: MAJOR
担当: {{assigned_team}}

影響:
- サービス: {{service_impact}}
- ユーザー: {{user_impact}}
- SLA: {{sla_impact}}

対応指示:
1. {{instruction_1}}
2. {{instruction_2}}
3. {{instruction_3}}

報告先: {{report_to}}
期限: {{deadline}}
```

---

## 📊 状況報告テンプレート

### 15分ごとの定期報告

```markdown
インシデント状況報告 #{{report_number}}

報告時刻: {{report_timestamp}}
経過時間: {{elapsed_time}}

【現在の状態】
- 全体進捗: {{overall_progress}}%
- 復旧フェーズ: {{current_phase}}
- 次のマイルストーン: {{next_milestone}}

【完了項目】
{{completed_items}}

【実施中項目】
{{in_progress_items}}

【課題・リスク】
{{issues_and_risks}}

【次回報告予定】
{{next_report_time}}
```

### Elder Council向け要約報告

```markdown
Elder Council インシデント要約

エグゼクティブサマリー:
{{executive_summary}}

ビジネスインパクト:
- 収益影響: {{revenue_impact}}
- ユーザー影響: {{user_satisfaction_impact}}
- ブランド影響: {{brand_impact}}

技術的詳細:
- 根本原因: {{root_cause}}
- 実施済み対策: {{implemented_measures}}
- 恒久対策: {{permanent_solutions}}

意思決定必要事項:
{{decision_required_items}}

推奨アクション:
{{recommended_actions}}
```

---

## 🔄 復旧完了通知テンプレート

### 内部通知

```markdown
【完了】インシデント復旧完了通知

インシデントID: {{incident_id}}
復旧完了時刻: {{recovery_timestamp}}
総ダウンタイム: {{total_downtime}}

復旧内容:
{{recovery_summary}}

検証結果:
- システムヘルス: {{health_check_result}}
- データ整合性: {{data_integrity_result}}
- パフォーマンス: {{performance_result}}

事後対応:
1. ポストモーテム: {{postmortem_schedule}}
2. 改善提案締切: {{improvement_deadline}}
3. フォローアップ: {{followup_schedule}}

お疲れ様でした。
```

### 外部通知

```markdown
件名: 【復旧完了】AI Companyサービス復旧のお知らせ

お客様各位

先ほどお知らせしておりました障害につきまして、
{{recovery_timestamp}}をもちまして、全サービスの復旧が
完了いたしましたことをご報告申し上げます。

【復旧内容】
{{recovery_details}}

【今後の対策】
{{prevention_measures}}

【お詫び】
この度は、お客様に多大なるご迷惑をおかけしましたこと、
深くお詫び申し上げます。

今後このような事態が発生しないよう、
システムの改善に努めてまいります。

AI Company
カスタマーサポート
```

---

## 📱 マルチチャネル配信設定

### Slack通知フォーマット

```json
{
  "channel": "#incident-{{severity}}",
  "username": "Emergency Bot",
  "icon_emoji": ":rotating_light:",
  "attachments": [
    {
      "color": "{{color_by_severity}}",
      "title": "{{incident_title}}",
      "fields": [
        {
          "title": "Severity",
          "value": "{{severity}}",
          "short": true
        },
        {
          "title": "Impact",
          "value": "{{impact}}",
          "short": true
        }
      ],
      "actions": [
        {
          "text": "View Details",
          "url": "{{incident_url}}"
        },
        {
          "text": "Join War Room",
          "url": "{{warroom_url}}"
        }
      ]
    }
  ]
}
```

### Email配信設定

```yaml
email_config:
  disaster:
    priority: "urgent"
    importance: "high"
    headers:
      X-Priority: "1"
      X-MSMail-Priority: "High"
    reply_to: "emergency@aicompany.com"
    
  critical:
    priority: "high"
    importance: "high"
    headers:
      X-Priority: "2"
    
  major:
    priority: "normal"
    importance: "normal"
```

---

## 🌐 多言語対応

### 言語別テンプレート管理

```python
# multilingual_templates.py

TEMPLATES = {
    "ja": {
        "disaster": {
            "subject": "【最重要】システム障害発生",
            "greeting": "お客様各位",
            "apology": "ご迷惑をおかけし、深くお詫び申し上げます。"
        }
    },
    "en": {
        "disaster": {
            "subject": "[CRITICAL] System Outage",
            "greeting": "Dear Customers",
            "apology": "We sincerely apologize for any inconvenience."
        }
    }
}
```

---

## ✅ 使用上の注意

1. **テンプレート変数**
   - 必ず{{}}で囲まれた変数を適切な値に置換
   - 未定の場合は「確認中」や「TBD」を使用

2. **配信タイミング**
   - Disaster: 検知から5分以内
   - Critical: 検知から15分以内
   - Major: 検知から30分以内

3. **承認プロセス**
   - Disaster外部通知: Grand Elder承認必須
   - Critical外部通知: Elder Council承認必須
   - Major外部通知: インシデントコマンダー承認

4. **記録保持**
   - 全ての通知は自動的にアーカイブ
   - 監査証跡として最低1年間保管

---

**承認**: Grand Elder maru  
**文書番号**: ECT-001  
**次回レビュー**: 2025年8月10日