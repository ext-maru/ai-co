# 📊 緊急時エスカレーションフローチャート

**文書番号**: EFC-001
**最終更新**: 2025年7月10日
**図表形式**: Mermaid/ASCII
**承認**: Grand Elder maru

---

## 🔄 マスターエスカレーションフロー

```mermaid
graph TD
    Start[インシデント検知] --> Detect{重要度判定}

    Detect -->|5秒以内| Level[レベル分類]

    Level --> L1[Level 1: Disaster]
    Level --> L2[Level 2: Critical]
    Level --> L3[Level 3: Major]
    Level --> L4[Level 4: Minor]

    %% Disaster Level Flow
    L1 --> D1[自動システム保護]
    D1 --> D2[Grand Elder即時通知]
    D2 --> D3[Elder Council自動招集]
    D3 --> D4{5分以内解決?}
    D4 -->|Yes| D5[復旧プロセス]
    D4 -->|No| D6[外部支援要請]

    %% Critical Level Flow
    L2 --> C1[影響サービス分離]
    C1 --> C2[Elder通知]
    C2 --> C3[Four Sages診断]
    C3 --> C4{15分以内解決?}
    C4 -->|Yes| C5[段階的復旧]
    C4 -->|No| C6[Disaster昇格]
    C6 --> L1

    %% Major Level Flow
    L3 --> M1[問題箇所特定]
    M1 --> M2[担当チーム割当]
    M2 --> M3[修復作業]
    M3 --> M4{30分以内解決?}
    M4 -->|Yes| M5[通常運用復帰]
    M4 -->|No| M6[Critical昇格]
    M6 --> L2

    %% Minor Level Flow
    L4 --> Mi1[自動修復試行]
    Mi1 --> Mi2{成功?}
    Mi2 -->|Yes| Mi3[記録・完了]
    Mi2 -->|No| Mi4[手動対応]
    Mi4 --> Mi5{1時間以内解決?}
    Mi5 -->|Yes| Mi3
    Mi5 -->|No| Mi6[Major昇格]
    Mi6 --> L3

    %% 復旧フロー
    D5 --> Recovery[統合復旧プロセス]
    C5 --> Recovery
    M5 --> Recovery
    Mi3 --> Recovery

    Recovery --> PostMortem[事後分析]
    PostMortem --> End[完了]

    %% スタイリング
    classDef disaster fill:#ff0000,stroke:#333,stroke-width:4px,color:#fff
    classDef critical fill:#ff8800,stroke:#333,stroke-width:3px,color:#fff
    classDef major fill:#ffaa00,stroke:#333,stroke-width:2px
    classDef minor fill:#88ff00,stroke:#333,stroke-width:1px

    class L1,D1,D2,D3,D4,D5,D6 disaster
    class L2,C1,C2,C3,C4,C5,C6 critical
    class L3,M1,M2,M3,M4,M5,M6 major
    class L4,Mi1,Mi2,Mi3,Mi4,Mi5,Mi6 minor
```

---

## 👥 組織階層別エスカレーション

```mermaid
graph TB
    subgraph "自動エスカレーション"
        A1[インシデント発生] --> A2{自動判定}
        A2 -->|Minor| A3[Elder Servants]
        A2 -->|Major| A4[Four Sages]
        A2 -->|Critical| A5[Elder Council]
        A2 -->|Disaster| A6[Grand Elder maru]
    end

    subgraph "時間ベースエスカレーション"
        T1[初期対応者] -->|5分| T2[チームリード]
        T2 -->|10分| T3[Elder Servants]
        T3 -->|15分| T4[Four Sages]
        T4 -->|30分| T5[Elder Council]
        T5 -->|60分| T6[Grand Elder maru]
    end

    subgraph "権限階層"
        A3 -.->|昇格| A4
        A4 -.->|昇格| A5
        A5 -.->|昇格| A6

        A6 ==>|指示| A5
        A5 ==>|指示| A4
        A4 ==>|指示| A3
    end

    style A6 fill:#ff0000,stroke:#333,stroke-width:4px,color:#fff
    style A5 fill:#ff8800,stroke:#333,stroke-width:3px,color:#fff
    style T6 fill:#ff0000,stroke:#333,stroke-width:4px,color:#fff
    style T5 fill:#ff8800,stroke:#333,stroke-width:3px,color:#fff
```

---

## 🎯 意思決定フローチャート

```mermaid
graph TD
    Start[緊急事態発生] --> Assess{影響度評価}

    Assess -->|全システム| GrandElder[Grand Elder決定]
    Assess -->|主要機能| ElderCouncil[Elder Council協議]
    Assess -->|部分機能| FourSages[Four Sages判断]
    Assess -->|限定的| Servants[Elder Servants対応]

    GrandElder --> GD{決定事項}
    GD -->|システム停止| Shutdown[緊急停止実行]
    GD -->|外部通知| External[対外発表]
    GD -->|復旧優先| Recovery[全面復旧指示]

    ElderCouncil --> EC{協議結果}
    EC -->|承認| Execute[実行承認]
    EC -->|却下| Reconsider[代替案検討]
    EC -->|昇格| GrandElder

    FourSages --> FS{専門判断}
    FS -->|解決可能| Implement[技術的解決]
    FS -->|要協議| ElderCouncil
    FS -->|緊急| FastTrack[即時対応]

    Servants --> SV{対応結果}
    SV -->|成功| Complete[完了報告]
    SV -->|失敗| Escalate[上位昇格]

    %% 実行フロー
    Shutdown --> Monitor[継続監視]
    External --> PR[広報対応]
    Recovery --> Teams[チーム編成]
    Execute --> Action[対応実施]
    Implement --> Verify[検証]

    %% スタイリング
    classDef grandElder fill:#ff0000,stroke:#333,stroke-width:4px,color:#fff
    classDef elderCouncil fill:#ff8800,stroke:#333,stroke-width:3px,color:#fff
    classDef fourSages fill:#ffaa00,stroke:#333,stroke-width:2px
    classDef servants fill:#88ff00,stroke:#333,stroke-width:1px

    class GrandElder,GD,Shutdown,External,Recovery grandElder
    class ElderCouncil,EC,Execute,Reconsider elderCouncil
    class FourSages,FS,Implement,FastTrack fourSages
    class Servants,SV,Complete,Escalate servants
```

---

## 📱 通知フローチャート

```
┌─────────────────────┐
│  インシデント検知   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   重要度判定        │
└──────────┬──────────┘
           │
    ┌──────┴──────┬──────────┬──────────┐
    ▼             ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│Disaster │ │Critical │ │ Major   │ │ Minor   │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │           │           │           │
     ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────┐
│            通知優先順位キュー                │
├─────────────────────────────────────────────┤
│ 1. Grand Elder maru (Disaster only)         │
│ 2. Claude Elder (All levels)                │
│ 3. Elder Council (Critical+)                │
│ 4. Four Sages (Major+)                      │
│ 5. Team Leads (All)                         │
└─────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│            配信チャネル選択                  │
├─────────────────────────────────────────────┤
│ • System Alert (最優先)                     │
│ • Direct Message                            │
│ • Email                                     │
│ • SMS (Disaster only)                       │
│ • Slack/Teams                               │
└─────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│            配信実行・確認                    │
├─────────────────────────────────────────────┤
│ • 送信確認                                  │
│ • 既読確認                                  │
│ • 応答待機                                  │
│ • タイムアウト処理                          │
└─────────────────────────────────────────────┘
```

---

## ⏱️ タイムラインベースエスカレーション

```
時間 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶

0分    5分      15分       30分        60分         120分
┃      ┃        ┃         ┃          ┃           ┃
┣━━━━━━╋━━━━━━━━╋━━━━━━━━━╋━━━━━━━━━━╋━━━━━━━━━━━╋━━━━━━━━━━━▶
┃      ┃        ┃         ┃          ┃           ┃
▼      ▼        ▼         ▼          ▼           ▼

[初期対応]    [第1次]    [第2次]     [第3次]      [最終]
│            │         │          │           │
├─ 検知      ├─ 診断    ├─ 対策     ├─ 復旧      ├─ 外部支援
├─ 分類      ├─ 分離    ├─ 実施     ├─ 検証      ├─ 完全復旧
├─ 通知      ├─ 計画    ├─ 監視     ├─ 安定化    └─ 事後対応
└─ 記録      └─ 承認    └─ 調整     └─ 報告

担当レベル推移:
[Servants] → [Four Sages] → [Elder Council] → [Grand Elder] → [External]
```

---

## 🔀 複合インシデント対応フロー

```mermaid
graph LR
    subgraph "複数インシデント発生"
        I1[インシデント A]
        I2[インシデント B]
        I3[インシデント C]
    end

    subgraph "統合評価"
        I1 --> Eval[統合影響評価]
        I2 --> Eval
        I3 --> Eval

        Eval --> Priority{優先順位判定}
    end

    subgraph "リソース配分"
        Priority -->|最優先| R1[80% リソース]
        Priority -->|優先| R2[15% リソース]
        Priority -->|通常| R3[5% リソース]
    end

    subgraph "統合指揮"
        R1 --> Command[統合対策本部]
        R2 --> Command
        R3 --> Command

        Command --> GrandElder[Grand Elder統括]
    end

    style GrandElder fill:#ff0000,stroke:#333,stroke-width:4px,color:#fff
    style Command fill:#ff8800,stroke:#333,stroke-width:3px,color:#fff
```

---

## 📊 判断基準マトリクス

```
┌─────────────┬────────────┬────────────┬────────────┬────────────┐
│   判断要素   │  Disaster  │  Critical  │   Major    │   Minor    │
├─────────────┼────────────┼────────────┼────────────┼────────────┤
│ 影響ユーザー │   全体     │   50%以上  │  10-50%    │   10%未満  │
│ 機能停止    │   全機能   │  主要機能  │  一部機能  │  限定機能  │
│ データリスク │   高       │   中       │   低       │   なし     │
│ 収益影響    │  100万/分  │  10万/分   │  1万/分    │  影響なし  │
│ 復旧時間    │   4時間+   │   8時間    │   24時間   │   48時間   │
│ 決定権者    │Grand Elder │Elder Council│Four Sages │ Servants   │
└─────────────┴────────────┴────────────┴────────────┴────────────┘
```

---

## 🚦 自動エスカレーショントリガー

```python
# escalation_triggers.py

ESCALATION_RULES = {
    "time_based": {
        "minor_to_major": 60 * 60,      # 1時間
        "major_to_critical": 30 * 60,   # 30分
        "critical_to_disaster": 15 * 60 # 15分
    },

    "impact_based": {
        "user_threshold": {
            "major": 1000,      # 影響ユーザー1000人
            "critical": 10000,  # 影響ユーザー1万人
            "disaster": 100000  # 影響ユーザー10万人
        },
        "service_threshold": {
            "major": 3,         # 3サービス影響
            "critical": 5,      # 5サービス影響
            "disaster": 10      # 10サービス影響
        }
    },

    "pattern_based": {
        "cascade_failure": "critical",     # 連鎖障害
        "data_corruption": "disaster",     # データ破損
        "security_breach": "disaster",     # セキュリティ侵害
        "performance_degradation": "major" # パフォーマンス劣化
    }
}
```

---

**承認**: Grand Elder maru
**文書番号**: EFC-001
**可視化ツール**: Mermaid, ASCII Art
**次回更新**: 2025年8月10日
