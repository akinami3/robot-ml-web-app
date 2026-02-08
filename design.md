# AMR SaaS Web Application 設計書

## 1. 概要

本システムは、商用AMR（自律移動ロボット）を対象としたSaaS型管制システムです。  
Fleet Gatewayをエッジに配置し、MQTTとVendor APIを中心とした疎結合構成を採用しています。  
ブラックボックスAMRにも対応可能な設計です。

### 1.1 本書の構成

| セクション | 内容 |
|-----------|------|
| 2〜14章 | **MVP（最小実行可能製品）構成** |
| 15章 | **将来拡張（Future）** |

---

## 2. システムアーキテクチャ

### 2.1 全体構成図

```
[Frontend (Next.js)]
        │
        │ REST / WebSocket
        ▼
[Backend (FastAPI)]
        │
        │ gRPC (双方向ストリーミング)
        ▼
[Fleet Gateway (Go)]
        │
        │ MQTT / Vendor API
        ▼
[AMR (複数メーカー対応)]
```

### 2.2 レイヤー構成

| レイヤー | 技術 | 役割 |
|---------|------|------|
| Frontend | Next.js (React + TypeScript) | UI・状態表示・ミッション投入 |
| Backend | Python + FastAPI | API・認証・データ管理 |
| Fleet Gateway | Python (または Go) | リアルタイム制御・プロトコル変換 |
| Database | PostgreSQL / Redis | データ永続化・キャッシュ |
| Message Broker | MQTT (EMQX / Mosquitto) | 非同期通信・イベント配信 |

---

## 3. フロントエンド

### 3.1 技術選定

| 項目 | 選定技術 | 理由 |
|------|----------|------|
| フレームワーク | React + Next.js | SaaSのデファクト、SSR/SSG対応 |
| 言語 | TypeScript | 型安全性、保守性向上 |
| 状態管理 | TanStack Query + Zustand | サーバー状態とUI状態の分離 |
| 可視化 | Recharts | ダッシュボード・分析表示 |
| UIコンポーネント | shadcn/ui + Tailwind CSS | カスタマイズ性、一貫したデザイン |

### 3.2 主要機能

- AMR状態監視（リアルタイム）
- ミッション投入・管理
- ログ・分析表示
- ユーザー管理

### 3.3 通信方式

| 用途 | プロトコル |
|------|------------|
| 操作・設定 | REST (HTTP + JSON) |
| 状態表示 | WebSocket |

---

## 4. バックエンド

### 4.1 技術選定

| 項目 | 選定技術 | 理由 |
|------|----------|------|
| 言語 | Python | ML / RAGとの相性最強 |
| フレームワーク | FastAPI | 非同期処理対応、OpenAPI自動生成 |
| ORM | SQLAlchemy / SQLModel | PostgreSQL連携 |
| バリデーション | Pydantic v2 | 高速、型安全なデータ検証 |

### 4.2 主要機能

- 認証・認可（JWT）
- Fleet管理API
- データAPI（CRUD）
- ログ収集

### 4.3 API設計方針

- RESTful設計
- OpenAPI (Swagger) によるドキュメント自動生成
- バージョニング対応（/api/v1/）

---

## 5. Fleet Gateway

### 5.1 技術選定

| 項目 | 選定技術 | 理由 |
|------|----------|------|
| 言語 | Go | 並行処理強い、gRPC親和性、軽量 |
| gRPCサーバー | grpc-go | Backend連携（双方向ストリーミング） |
| 状態管理 | FSM | ロボット状態遷移管理 |
| 通信 (AMR向け) | MQTT Client (paho) | 非同期メッセージング |

### 5.2 コンポーネント構成

| コンポーネント | 技術 | 役割 |
|----------------|------|------|
| gRPCサーバー | grpc-go | Backend連携（コマンド受信・状態配信） |
| 通信 (AMR) | MQTT Client (paho) | AMRへのメッセージ送受信 |
| 状態管理 | FSM | ロボット状態遷移 |
| Adapter | Vendor API Wrapper | メーカー差分吸収 |
| 監視 | Heartbeat / Timeout | 死活監視 |
| デプロイ | Docker | コンテナ化 |

### 5.3 マルチメーカー対応（Adapter Pattern）★ポートフォリオ重要

```
Fleet Gateway
├── RobotController (interface)
│   ├── move()
│   ├── stop()
│   └── get_status()
│
├── VendorAAdapter (MQTT)
├── VendorBAdapter (REST)
└── VendorCAdapter (ROS2)
```

**設計ポイント**：
- 共通インターフェースでメーカー差分を吸収
- 新規メーカー追加時はAdapterのみ実装
- Backend/Frontendは変更不要

### 5.4 共通ロボットモデル

```json
{
  "id": "robot_001",
  "pose": { "x": 10.5, "y": 5.2, "theta": 1.57 },
  "battery": 85,
  "state": "MOVING",
  "capabilities": {
    "supports_pause": true,
    "supports_docking": true
  }
}
```

### 5.5 共通状態定義

| 状態 | 説明 |
|------|------|
| IDLE | 待機中 |
| MOVING | 移動中 |
| PAUSED | 一時停止 |
| ERROR | エラー |
| CHARGING | 充電中 |

---

## 6. 通信プロトコル

### 6.1 Frontend ↔ Backend

| 用途 | プロトコル | 特徴 |
|------|------------|------|
| CRUD・設定 | REST | 実装簡単、デバッグ容易 |
| リアルタイム状態 | WebSocket | 双方向、プッシュ通知 |

### 6.2 Backend ↔ Fleet Gateway

| 用途 | プロトコル | 特徴 |
|------|------------|------|
| コマンド送信 | gRPC (Unary) | 同期、型安全 |
| 状態ストリーム | gRPC (Server Streaming) | リアルタイム状態配信 |
| 双方向通信 | gRPC (Bidirectional) | 高性能、低遅延 |

**gRPC採用理由**：
- Protocol Buffersによる型安全・高速シリアライズ
- 双方向ストリーミングでリアルタイム性確保
- Go/Pythonでの高品質ライブラリ

### 6.3 Fleet Gateway ↔ AMR

| 用途 | プロトコル | 備考 |
|------|------------|------|
| 制御・状態 | Vendor API | REST / MQTT（ベンダ依存） |

**設計方針**：Adapterで吸収し、Gateway内部は統一インターフェース

---

## 7. データベース

### 7.1 MVP構成

| 用途 | DB | 理由 |
|------|-----|------|
| 業務データ | PostgreSQL | ACID保証、複雑クエリ対応 |
| キャッシュ | Redis | リアルタイム状態表示 |

### 7.2 業務データ（PostgreSQL）

- 操作履歴
- タスク管理
- ユーザー情報
- ミッション定義
- センサ・ログデータ

---

## 8. セキュリティ

### 8.1 通信セキュリティ

| 対象 | 技術 | 説明 |
|------|------|------|
| Frontend ↔ Backend | TLS | HTTPS通信暗号化 |
| Backend ↔ Gateway | TLS | 暗号化通信 |

### 8.2 認証・認可

| 技術 | 用途 |
|------|------|
| JWT | API認証、セッション管理 |
| RBAC | 操作権限の粒度管理 |

### 8.3 境界設計

```
[Cloud]
   │
   │ TLS
   ▼
[Fleet Gateway] ← 防波堤
   │
   │ ローカルネットワーク
   ▼
[AMR]
```

**原則**：AMRは直接クラウドに出さない。Fleet Gatewayが防波堤として機能。

---

## 9. コンテナ・デプロイ

### 9.1 技術選定

| 環境 | 技術 |
|------|------|
| 開発・本番 | Docker + Docker Compose |
| エッジ | Docker |

### 9.2 コンテナ構成

```yaml
# docker-compose.yml
services:
  frontend:
    image: frontend:latest
    ports: ["3000:3000"]
  
  backend:
    image: backend:latest
    ports: ["8000:8000"]
  
  gateway:
    image: gateway:latest
  
  postgres:
    image: postgres:15
    volumes: ["postgres_data:/var/lib/postgresql/data"]
  
  redis:
    image: redis:7
  
  mqtt-broker:
    image: eclipse-mosquitto:2
    ports: ["1883:1883"]
```

---

## 10. CI/CD

### 10.1 技術選定

| 項目 | 技術 |
|------|------|
| CI/CDツール | GitHub Actions |
| コンテナレジストリ | GitHub Container Registry |

### 10.2 パイプライン

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint
        run: |
          npm run lint          # Frontend
          ruff check .          # Backend
      - name: Test
        run: |
          npm test              # Frontend
          pytest                # Backend
  
  build-push:
    needs: lint-test
    runs-on: ubuntu-latest
    steps:
      - name: Build & Push Docker Images
        run: |
          docker build -t ghcr.io/${{ github.repository }}/frontend .
          docker push ghcr.io/${{ github.repository }}/frontend
```

---

## 11. 可観測性（基本）

### 11.1 MVP構成

| 要素 | 技術 | 用途 |
|------|------|------|
| メトリクス | Prometheus + Grafana | システム監視、ダッシュボード |
| ログ | Docker logs + ファイル出力 | 基本的なログ管理 |
| ヘルスチェック | /health エンドポイント | 死活監視 |

### 11.2 主要メトリクス

| カテゴリ | メトリクス例 |
|----------|---------------|
| AMR状態 | 稼働率、バッテリー推移、エラー率 |
| Fleet | 総台数、稼働中台数、タスク完了率 |
| Backend | APIレイテンシ、エラー率 |

---

## 12. シミュレーション

### 12.1 技術選定

| 用途 | 技術 |
|------|------|
| ROS2シミュレーション | Gazebo + ROS2 |
| 簡易シミュレーション | MockAdapter |

### 12.2 切替方式

```
Fleet Gateway
├── RealRobotAdapter (実機)
├── SimulatorAdapter (Gazebo)
└── MockAdapter (単体テスト用)
```

---

## 13. 設計思想

### 13.1 基本方針

| 観点 | 内容 |
|------|------|
| 分離と責務の明確化 | Gateway：リアルタイム制御<br>Backend：非リアルタイム処理<br>Frontend：UI表示 |
| リアルタイム vs 非リアルタイム | 制御はGateway、DB保存・分析はBackend |
| 可用性と堅牢性 | Gateway防波堤、DB用途別分離 |
| 拡張性 | マルチメーカー対応 (Adapter Pattern) |
| セキュリティ | TLS + JWT + RBAC |

### 13.2 デザインパターン（MVP）

| パターン | 用途 |
|----------|------|
| Layered Architecture | Frontend/Backend/Gateway/AMRの層分離 |
| Facade Pattern | Gatewayが複雑プロトコルを統一IF化 |
| Adapter Pattern | マルチメーカー対応★ |
| Strategy Pattern | AMRごとのアルゴリズム切替 |
| Repository Pattern | DBアクセス抽象化 |
| gRPC Streaming | Backend↔Gateway間リアルタイム通信 |
| Pub/Sub | Gateway↔AMR間MQTTでリアルタイム通知 |

---

## 14. 技術スタック一覧（MVP）

| カテゴリ | 技術 |
|----------|------|
| Frontend | Next.js, TypeScript, TanStack Query, Zustand, shadcn/ui |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic v2, grpcio |
| Gateway | Go, grpc-go, paho.mqtt.golang |
| Database | PostgreSQL, Redis |
| 通信 | REST, WebSocket, gRPC, MQTT |
| セキュリティ | TLS, JWT, RBAC |
| コンテナ | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| 可観測性 | Prometheus, Grafana |
| シミュレーション | Gazebo, ROS2 |

---

# 15. 将来拡張（Future）

本章では、MVP後に段階的に導入を検討する技術・設計を記載します。

---

## 15.1 インフラ・デプロイ拡張

### Kubernetes移行

| 項目 | 技術 | 用途 |
|------|------|------|
| オーケストレーション | Kubernetes / k3s | 本番スケール、自動復旧 |
| エッジ | k3s | 軽量Kubernetes |
| Service Mesh | Istio / Linkerd | トラフィック制御、mTLS自動化 |

### GitOps

| 技術 | 用途 |
|------|------|
| ArgoCD / Flux | 宣言的デプロイ、監査性向上 |
| Kustomize / Helm | 環境別設定管理 |

### リリース戦略

| 戦略 | 技術 | 用途 |
|------|------|------|
| Canary Deploy | Flagger | 段階的リリース |
| Blue-Green | Kubernetes | 即時ロールバック |
| Feature Flags | Unleash | A/Bテスト |

---

## 15.2 セキュリティ強化

| 技術 | 用途 | 優先度 |
|------|------|--------|
| OAuth2 | SaaS連携、外部認証 | 高 |
| VPN (WireGuard) | Gateway-AMR間閉域通信 | 高 |
| ABAC (OPA) | 属性ベース認可 | 中 |
| mTLS | サービス間相互認証 | 中 |
| HashiCorp Vault | Secret管理 | 中 |
| Zero Trust | アイデンティティベースアクセス | 低 |

---

## 15.3 可観測性強化

### OpenTelemetry統合

```
[Application]
      │
      │ OpenTelemetry SDK
      ▼
[OpenTelemetry Collector]
      │
      ├── Traces  → Jaeger / Tempo
      ├── Metrics → Prometheus → Grafana
      └── Logs    → Loki → Grafana
```

| 技術 | 用途 | 優先度 |
|------|------|--------|
| OpenTelemetry | 統合計装 | 高 |
| Jaeger | 分散トレーシング | 高 |
| Loki | ログ集約 | 中 |
| Alertmanager | アラート管理 | 中 |
| APM (Datadog) | 商用監視 | 低 |

---

## 15.4 耐障害性・信頼性

### Circuit Breaker

| パターン | 用途 | 実装技術 |
|----------|------|------------|
| Circuit Breaker | AMR障害時の連鎖障害防止 | gobreaker / tenacity |
| Retry | 一時的な障害の自動復旧 | Exponential Backoff |
| Timeout | 応答なしへの対応 | Context Deadline |
| Bulkhead | 障害分離 | コネクションプール分離 |

### Circuit Breaker状態遷移

```
[Closed] --失敗閾値超過--> [Open]
   ▲                           │
   │                     タイムアウト後
   │                           ▼
   └──── 成功 ──── [Half-Open]
```

---

## 15.5 データ設計強化

### 時系列データベース

| 技術 | 用途 | 優先度 |
|------|------|--------|
| TimescaleDB | センサ・ログの時系列保存 | 高 |
| InfluxDB | 軽量時系列DB | 中 |

### RAG/ML基盤

| 技術 | 用途 | 優先度 |
|------|------|--------|
| pgvector | ベクトル検索（小規模） | 高 |
| Milvus / Qdrant | ベクトル検索（大規模） | 中 |
| Llama / Mistral | ローカルLLM | 中 |
| sentence-transformers | Embedding | 高 |

### 高度なデータパターン

| パターン | 用途 | 優先度 |
|----------|------|--------|
| Event Sourcing | 完全な監査証跡、状態復元 | 低 |
| Outbox Pattern | DB保存とイベント発行の保証 | 低 |
| CDC (Debezium) | リアルタイムデータ同期 | 低 |
| Saga Pattern | 分散トランザクション整合性 | 低 |
| CQRS | 読み書き分離 | 中 |

---

## 15.6 スケーリング

| 規模 | AMR台数 | 推奨構成 |
|------|---------|----------|
| 小規模 | ~50台 | 単一Gateway + Docker Compose （MVP） |
| 中規模 | 50~500台 | 複数Gateway + Kubernetes |
| 大規模 | 500台以上 | 分散Gateway + Kafka + 専用VectorDB |

### 水平スケーリング

| コンポーネント | スケール方法 |
|----------------|----------------|
| Frontend | CDN + Auto Scaling |
| Backend | Kubernetes HPA |
| Gateway | エッジごとに分散配置 |
| Database | Read Replica + Connection Pool |

---

## 15.7 テスト強化

### テストピラミッド

```
          /\
         /  \  E2Eテスト (Playwright)
        /----\
       /      \  統合テスト (TestContainers)
      /--------\
     /          \  単体テスト (pytest/Jest)  ← MVP
    /--------------\
```

| テスト種別 | 技術 | 優先度 |
|----------|------|--------|
| 単体テスト | pytest / Jest | MVP |
| 統合テスト | TestContainers | 高 |
| E2Eテスト | Playwright | 中 |
| 契約テスト | Pact | 低 |
| 負荷テスト | k6 / Locust | 中 |
| カオステスト | Litmus | 低 |

---

## 15.8 通信プロトコル拡張

| 技術 | 用途 | 優先度 |
|------|------|--------|
| gRPC | Backend-Gateway間高速通信 | 中 |
| NATS | 低遅延メッセージング | 低 |
| Kafka | 大規模ログ・イベント配信 | 低 |
| GraphQL | 複雑なフロントエンドクエリ | 低 |

---

## 15.9 Gateway言語拡張

| 言語 | 用途 | 優先度 |
|------|------|--------|
| Go | 高並行処理、本番最適化 | 高 |
| Rust | 超高性能、メモリ安全性 | 低 |

---

## 15.10 アーキテクチャパターン拡張

| パターン | 用途 | 優先度 |
|----------|------|--------|
| Hexagonal Architecture | 外部依存の分離 | 中 |
| Event-Driven Architecture | 疎結合化、スケーラビリティ | 中 |
| Domain-Driven Design (DDD) | 複雑ドメインの整理 | 低 |
| Microservices | 機能分割、独立デプロイ | 低 |

---

## 15.11 拡張ロードマップ

### Phase 1（製品リリース後 3ヶ月）
- [ ] OAuth2認証
- [ ] TimescaleDB導入
- [ ] OpenTelemetry + Jaeger
- [ ] 統合テスト（TestContainers）

### Phase 2（6ヶ月）
- [ ] Kubernetes移行
- [ ] Circuit Breaker実装
- [ ] RAG基盤（pgvector + LLM）
- [ ] VPN (WireGuard)

### Phase 3（12ヶ月）
- [ ] GitOps (ArgoCD)
- [ ] Canary Deploy
- [ ] 大規模スケーリング対応
- [ ] Event Sourcing / CQRS

---

## 付録：設計書サマリー（面接・プレゼン用）

> **MVP構成**  
> 本システムはレイヤードアーキテクチャを基本とし、リアルタイム制御はGateway、非リアルタイム処理はBackendに分離しています。  
> AMRごとの複雑なプロトコルはGatewayでAdapter/Strategyパターンを適用して統一し、マルチメーカー対応を実現しています。  
> TLS/JWT/RBACによる認証・認可とFleet Gatewayによる境界設計で、セキュリティを確保しています。

> **将来拡張**  
> Kubernetes/GitOpsによるスケーラブルなインフラ、OpenTelemetryによる可観測性、Circuit Breakerによる耐障害性、Event Sourcing/CQRSによるデータ整合性など、エンタープライズグレードへの拡張パスを設計しています。

---

*Document Version: 3.0 (MVP Edition)*  
*Last Updated: 2026-02-07*
