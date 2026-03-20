# Robot AI Web Application — 総合学習ガイド

> **対象**: プログラミング初心者  
> **プロジェクト**: robot-ml-web-app  
> **言語**: TypeScript (React), Python (FastAPI), Go (WebSocket Gateway)

---

## 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [ディレクトリ構造](#2-ディレクトリ構造)
3. [TypeScript / React フロントエンド](#3-typescript--react-フロントエンド)
4. [Python / FastAPI バックエンド](#4-python--fastapi-バックエンド)
5. [Go ゲートウェイ](#5-go-ゲートウェイ)
6. [データベース (PostgreSQL)](#6-データベース-postgresql)
7. [Protocol Buffers](#7-protocol-buffers)
8. [デザインパターン](#8-デザインパターン)
9. [セキュリティ](#9-セキュリティ)
10. [Docker / インフラ](#10-docker--インフラ)
11. [CI/CD](#11-cicd)
12. [WebSocket リアルタイム通信](#12-websocket-リアルタイム通信)
13. [RAG (検索拡張生成)](#13-rag-検索拡張生成)
14. [安全機能](#14-安全機能)
15. [テスト](#15-テスト)
16. [用語集](#16-用語集)

---

## 1. プロジェクト概要

### このアプリは何をするの？

ロボットをWeb ブラウザから操作・監視するアプリです。

```
┌─────────────┐    WebSocket     ┌──────────┐    Redis     ┌──────────┐
│  ブラウザ    │ ◄──────────────► │ Gateway  │ ◄──────────► │ Backend  │
│  (React)    │                  │  (Go)    │              │ (Python) │
└─────────────┘                  └──────────┘              └──────────┘
                                                                │
                                                           ┌────▼─────┐
                                                           │PostgreSQL│
                                                           │ + Redis  │
                                                           │ + Ollama │
                                                           └──────────┘
```

**3つのサービス構成**:
- **Frontend** (React + TypeScript): ユーザーが触るUI
- **Backend** (Python + FastAPI): データの保存・認証・AI
- **Gateway** (Go): ロボットとのリアルタイム通信

---

## 2. ディレクトリ構造

```
robot-ml-web-app/
├── frontend/                 # フロントエンド (React)
│   ├── src/
│   │   ├── main.tsx         # アプリのエントリーポイント
│   │   ├── App.tsx          # ルーティング定義
│   │   ├── components/      # 再利用可能なUIパーツ
│   │   ├── pages/           # 各画面
│   │   ├── stores/          # 状態管理 (Zustand)
│   │   ├── services/        # API通信
│   │   ├── hooks/           # カスタムフック
│   │   ├── types/           # 型定義
│   │   └── lib/             # ユーティリティ
│   ├── package.json         # npm依存関係
│   ├── vite.config.ts       # ビルド設定
│   └── tailwind.config.js   # CSSフレームワーク設定
│
├── backend/                  # バックエンド (Python)
│   ├── app/
│   │   ├── main.py          # FastAPIアプリ起動
│   │   ├── config.py        # 設定管理
│   │   ├── core/            # セキュリティ等の基盤
│   │   ├── api/v1/          # APIエンドポイント
│   │   ├── domain/          # ビジネスロジック
│   │   │   ├── entities/    # データの型定義
│   │   │   ├── repositories/# DB操作の抽象インターフェース
│   │   │   └── services/    # ビジネスルール
│   │   └── infrastructure/  # 外部接続 (DB, Redis, LLM)
│   └── pyproject.toml       # Python依存関係
│
├── gateway/                  # ゲートウェイ (Go)
│   ├── cmd/gateway/main.go  # エントリーポイント
│   └── internal/
│       ├── adapter/         # ロボット接続アダプタ
│       ├── safety/          # 安全機能
│       ├── server/          # WebSocketサーバー
│       ├── protocol/        # メッセージ形式
│       ├── bridge/          # Redis連携
│       └── config/          # 設定
│
├── proto/                    # Protocol Buffers定義
├── docker-compose.yml        # コンテナ構成
├── .env.example              # 環境変数テンプレート
└── scripts/                  # 開発用スクリプト
```

---

## 3. TypeScript / React フロントエンド

### 3.1 TypeScript の基礎

TypeScript は JavaScript に「型」を追加した言語です。

```typescript
// ── 基本的な型 ──
let name: string = "Robot-1";     // 文字列型
let speed: number = 1.5;          // 数値型
let isActive: boolean = true;     // 真偽値型
let tags: string[] = ["lidar"];   // 配列型

// ── インターフェース（型の設計図）──
// types/index.ts より
interface Robot {
  id: string;              // ロボットの一意なID
  name: string;            // ロボットの名前
  adapter_type: string;    // 接続方式（"mock" など）
  status: RobotStatus;     // 現在の状態
  created_at: string;      // 作成日時
}

// ── 列挙型（決まった選択肢）──
type RobotStatus = "idle" | "moving" | "error" | "disconnected";
type UserRole = "admin" | "operator" | "viewer";
```

**初心者ポイント**: 型を付けると、間違ったデータを渡した時にエディタが教えてくれます。

### 3.2 React コンポーネント

React では画面を「コンポーネント」という部品に分けて作ります。

```tsx
// pages/LoginPage.tsx — ログイン画面の例
import { useState } from "react";           // 状態管理フック
import { useNavigate } from "react-router-dom"; // 画面遷移
import { authApi } from "@/services/api";    // API通信
import { useAuthStore } from "@/stores/authStore"; // 認証状態

export function LoginPage() {
  // ── 状態の定義 ──
  // useState<型>(初期値) で状態変数を作る
  const [email, setEmail] = useState("");        // メールアドレス
  const [password, setPassword] = useState("");  // パスワード
  const [error, setError] = useState("");        // エラーメッセージ
  const [loading, setLoading] = useState(false); // 読み込み中フラグ

  // ── 外部のツールを取得 ──
  const navigate = useNavigate();              // 画面遷移関数
  const { setTokens, setUser } = useAuthStore(); // 認証ストアの関数

  // ── ログイン処理 ──
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();         // ページリロードを防止
    setError("");               // エラーをクリア
    setLoading(true);           // ローディング開始

    try {
      // 1. ログインAPIを呼ぶ
      const res = await authApi.login(email, password);
      // 2. トークンを保存
      setTokens(res.data);
      // 3. ユーザー情報を取得
      const userRes = await authApi.me();
      setUser(userRes.data);
      // 4. ダッシュボードへ遷移
      navigate("/");
    } catch {
      setError("ログインに失敗しました");
    } finally {
      setLoading(false);        // ローディング終了
    }
  };

  // ── 画面の描画 ──
  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {error && <p className="text-red-500">{error}</p>}
      <button type="submit" disabled={loading}>
        {loading ? "ログイン中..." : "ログイン"}
      </button>
    </form>
  );
}
```

**重要な概念**:
| 概念 | 説明 | 例 |
|------|------|-----|
| `useState` | コンポーネント内の状態を管理 | `const [count, setCount] = useState(0)` |
| `useEffect` | 副作用（API呼び出し等）を実行 | `useEffect(() => { fetch() }, [])` |
| `props` | 親から子に渡すデータ | `<Button label="OK" />` |
| JSX | HTMLに似た構文でUIを記述 | `<div className="p-4">` |

### 3.3 API 通信 (Axios)

`api.ts` はバックエンドとの通信を担当するファイルです。

```typescript
// services/api.ts

import axios from "axios";
import { useAuthStore } from "@/stores/authStore";

// ── Axios インスタンスを作成 ──
// baseURL: すべてのリクエストのURLの先頭に付く
const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// ── リクエスト インターセプター ──
// すべてのリクエストが送信される前に実行される
api.interceptors.request.use((config) => {
  // ストアからアクセストークンを取得
  const token = useAuthStore.getState().accessToken;
  if (token) {
    // Authorization ヘッダーにトークンを追加
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── レスポンス インターセプター ──
// すべてのレスポンスを受け取った後に実行される
api.interceptors.response.use(
  (response) => response,  // 成功時: そのまま返す
  async (error) => {
    // 401エラー(認証切れ)の時、自動でトークンを更新
    if (error.response?.status === 401) {
      const store = useAuthStore.getState();
      if (store.refreshToken) {
        try {
          // リフレッシュトークンで新しいアクセストークンを取得
          const res = await axios.post("/api/v1/auth/refresh", {
            refresh_token: store.refreshToken,
          });
          store.setTokens(res.data);
          // 元のリクエストを新しいトークンで再実行
          error.config.headers.Authorization =
            `Bearer ${res.data.access_token}`;
          return api.request(error.config);
        } catch {
          store.logout();  // 更新も失敗 → ログアウト
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── API関数群 ──
// 各機能ごとにオブジェクトでまとめる
export const robotApi = {
  list: () => api.get<Robot[]>("/robots"),
  get: (id: string) => api.get<Robot>(`/robots/${id}`),
  create: (data: { name: string; adapter_type: string }) =>
    api.post<Robot>("/robots", data),
  delete: (id: string) => api.delete(`/robots/${id}`),
};
```

**初心者ポイント**: インターセプターは「全リクエストに共通する処理」を一箇所にまとめる仕組み。認証トークンの自動付与・自動更新ができる。

### 3.4 状態管理 (Zustand)

Zustand はシンプルな状態管理ライブラリです。

```typescript
// stores/authStore.ts

import { create } from "zustand";
import { persist } from "zustand/middleware";

// ── ストアの型定義 ──
interface AuthState {
  accessToken: string | null;    // アクセストークン
  refreshToken: string | null;   // リフレッシュトークン
  user: User | null;             // ユーザー情報
  isAuthenticated: boolean;      // ログイン済みか

  setTokens: (tokens: AuthTokens) => void;  // トークン設定
  setUser: (user: User) => void;             // ユーザー設定
  logout: () => void;                        // ログアウト
  hasRole: (...roles: UserRole[]) => boolean; // 権限チェック
}

// ── ストア作成 ──
export const useAuthStore = create<AuthState>()(
  persist(                      // persist: ブラウザを閉じてもデータを保持
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      setTokens: (tokens) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        }),

      // 可変長引数: 複数の権限のどれか一つに一致するか
      hasRole: (...roles) => {
        const user = get().user;
        return user ? roles.includes(user.role) : false;
      },
    }),
    {
      name: "robot-ai-auth",  // localStorageのキー名
      // 保存するフィールドを限定（セキュリティ上、最小限）
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
```

### 3.5 ルーティング (React Router)

`App.tsx` で「どのURLでどの画面を表示するか」を定義します。

```tsx
// App.tsx

import { Routes, Route, Navigate } from "react-router-dom";

// ── 認証ガード ──
// ログインしていない場合はログインページにリダイレクト
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  if (!accessToken) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      {/* 認証不要のページ */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      {/* 認証必要なページ（AppLayoutで共通レイアウトを適用） */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />  {/* サイドバー + ステータスバー */}
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="control" element={<ManualControlPage />} />
        <Route path="navigation" element={<NavigationPage />} />
        <Route path="sensors" element={<SensorViewPage />} />
        <Route path="data" element={<DataManagementPage />} />
        <Route path="rag" element={<RAGChatPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* 未定義のURLは / にリダイレクト */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
```

### 3.6 WebSocket フック

リアルタイム通信のためのカスタムフックです。

```typescript
// hooks/useWebSocket.ts

export function useWebSocket(robotId: string | null) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const maxReconnects = 10;

  useEffect(() => {
    if (!robotId) return;

    function connect() {
      const token = useAuthStore.getState().accessToken;
      // WebSocket URL にトークンをクエリパラメータで渡す
      const ws = new WebSocket(
        `${WS_URL}?robot_id=${robotId}&token=${token}`
      );

      ws.onopen = () => {
        setIsConnected(true);
        reconnectCount.current = 0;  // 接続成功でカウンタリセット
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        // メッセージの種類に応じて処理を分岐
        switch (msg.type) {
          case "sensor_data":
            updateSensorData(msg.payload);
            break;
          case "robot_status":
            updateRobotStatus(msg.payload);
            break;
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // 自動再接続（最大10回、3秒間隔）
        if (reconnectCount.current < maxReconnects) {
          reconnectCount.current++;
          setTimeout(connect, 3000);
        }
      };

      wsRef.current = ws;
    }

    connect();

    // クリーンアップ: コンポーネント破棄時に接続を閉じる
    return () => { wsRef.current?.close(); };
  }, [robotId]);

  // コマンド送信関数
  const sendCommand = useCallback((type: string, payload: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, payload }));
    }
  }, []);

  return { isConnected, sendCommand };
}
```


---

## 4. Python / FastAPI バックエンド

### 4.1 Python の基礎

```python
# ── 型ヒント（Type Hints）──
# Python 3.12 では型を明示的に書ける
def greet(name: str) -> str:
    return f"Hello, {name}"

# ── データクラス ──
from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class Robot:
    name: str                           # ロボット名
    adapter_type: str                   # 接続方式
    id: UUID = field(default_factory=uuid4)  # 自動生成ID
    status: str = "idle"                # デフォルト値

# ── 非同期処理（async/await）──
# I/O待ち時間（DB接続、API呼び出し）中に他の処理を進められる
async def get_robot(robot_id: UUID) -> Robot:
    result = await db.execute(select(RobotModel).where(...))
    return result.scalar_one()
```

### 4.2 FastAPI アプリケーション起動

```python
# app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

# ── ライフスパン（起動・終了処理）──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 起動時 ---
    await init_database()       # DB接続プール作成
    await init_redis(redis_url) # Redis接続
    await create_admin_user()   # 初期管理者作成
    yield                       # ← ここでアプリ稼働中
    # --- 終了時 ---
    await close_redis()         # Redis切断
    await close_database()      # DB切断

app = FastAPI(
    title="Robot AI Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# ── ヘルスチェック ──
@app.get("/health")
async def health():
    return {"status": "ok"}

# ── ルーター登録 ──
# 各機能のAPIをまとめて登録
app.include_router(router, prefix="/api/v1")
```

### 4.3 設定管理 (Pydantic Settings)

```python
# app/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """環境変数から設定を読み込むクラス"""
    
    # 各フィールドは環境変数名と対応
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://..."
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"
    
    # JWT設定
    jwt_algorithm: str = "RS256"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7
    jwt_private_key_path: str | None = None
    jwt_public_key_path: str | None = None
    
    # Ollama (LLM) 設定
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3"
    
    @property
    def jwt_private_key(self) -> str | None:
        """PEMファイルから秘密鍵を読み込む"""
        if self.jwt_private_key_path:
            return Path(self.jwt_private_key_path).read_text()
        return None
    
    model_config = {"env_file": ".env"}  # .envファイルからも読込可

@lru_cache  # キャッシュ: 同じ設定は一度だけ読み込む
def get_settings() -> Settings:
    return Settings()
```

**初心者ポイント**: `@lru_cache` は「一度計算した結果を覚えておく」デコレータ。設定は毎回ファイルを読む必要がないので効率的。

### 4.4 依存性注入 (Dependency Injection)

FastAPI の最も強力な機能の一つです。

```python
# api/v1/dependencies.py

from fastapi import Depends
from typing import Annotated

# ── ステップ1: DBセッションを取得 ──
async def get_db() -> AsyncSession:
    async for session in get_session():
        yield session

DbSession = Annotated[AsyncSession, Depends(get_db)]
# ↑ 「AsyncSession型で、get_dbで取得する」という意味

# ── ステップ2: リポジトリを取得（DBセッションに依存）──
def get_user_repo(session: DbSession) -> UserRepository:
    return SQLAlchemyUserRepository(session)
    #      ↑ 実装クラスを返す（抽象に依存、具体を注入）

UserRepo = Annotated[UserRepository, Depends(get_user_repo)]

# ── ステップ3: サービスを取得（リポジトリに依存）──
def get_dataset_service(
    dataset_repo: DatasetRepo,
    sensor_repo: SensorDataRepo,
) -> DatasetService:
    return DatasetService(dataset_repo, sensor_repo)

DatasetSvc = Annotated[DatasetService, Depends(get_dataset_service)]

# ── ステップ4: 認証（トークン検証 → ユーザー取得）──
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    user_repo: UserRepo,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = decode_token(credentials.credentials, settings.jwt_public_key)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await user_repo.get_by_id(UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

# ── ステップ5: 権限チェック ──
def require_role(*roles: UserRole):
    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker

AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
OperatorUser = Annotated[User, Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR))]
```

**依存性の連鎖**:
```
HTTPリクエスト
  → get_db()           → DBセッション
  → get_user_repo()    → UserRepository
  → get_current_user() → User（認証済み）
  → require_role()     → User（権限確認済み）
```

### 4.5 APIエンドポイント

```python
# api/v1/endpoints/robots.py

from fastapi import APIRouter

router = APIRouter(prefix="/robots", tags=["robots"])

@router.get("")
async def list_robots(
    user: CurrentUser,           # 認証必須
    robot_repo: RobotRepo,      # 自動注入
) -> list[RobotResponse]:
    """ロボット一覧を取得"""
    robots = await robot_repo.list_all()
    return [RobotResponse.from_entity(r) for r in robots]

@router.post("", status_code=201)
async def create_robot(
    data: RobotCreate,           # リクエストボディ（自動バリデーション）
    user: OperatorUser,          # operator以上の権限が必要
    robot_repo: RobotRepo,
    audit_svc: AuditSvc,
) -> RobotResponse:
    """新しいロボットを登録"""
    robot = Robot(name=data.name, adapter_type=data.adapter_type)
    created = await robot_repo.create(robot)
    
    # 監査ログを記録
    await audit_svc.log(
        user_id=user.id,
        action="robot.create",
        details={"robot_id": str(created.id)},
    )
    
    return RobotResponse.from_entity(created)

@router.delete("/{robot_id}")
async def delete_robot(
    robot_id: UUID,              # URLパスパラメータ（自動変換）
    user: AdminUser,             # admin権限が必要
    robot_repo: RobotRepo,
) -> dict:
    """ロボットを削除"""
    success = await robot_repo.delete(robot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Robot not found")
    return {"deleted": True}
```

### 4.6 ドメイン層（クリーンアーキテクチャ）

```python
# ── エンティティ（データの定義）──
# domain/entities/user.py

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

@dataclass
class User:
    username: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)


# ── リポジトリ（抽象インターフェース）──
# domain/repositories/user_repository.py

from abc import ABC, abstractmethod

class UserRepository(ABC):
    """ユーザーデータへのアクセスを定義する抽象クラス"""
    
    @abstractmethod
    async def get_by_id(self, id: UUID) -> User | None:
        """IDでユーザーを取得"""
        ...
    
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """メールアドレスでユーザーを取得"""
        ...
    
    @abstractmethod
    async def create(self, entity: User) -> User:
        """新しいユーザーを作成"""
        ...


# ── リポジトリ実装（SQLAlchemy）──
# infrastructure/database/repositories/user_repo.py

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session  # DBセッションを保持
    
    async def get_by_id(self, id: UUID) -> User | None:
        model = await self._session.get(UserModel, id)
        return self._to_entity(model) if model else None
    
    async def create(self, entity: User) -> User:
        model = UserModel(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            hashed_password=entity.hashed_password,
            role=entity.role.value,
        )
        self._session.add(model)
        await self._session.flush()  # DBに書き込み（コミットはまだ）
        return self._to_entity(model)
```

### 4.7 ORM モデル (SQLAlchemy)

```python
# infrastructure/database/models.py

from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, JSON, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class SensorDataModel(Base):
    __tablename__ = "sensor_data"
    # TimescaleDB ハイパーテーブル (時系列データの高速処理)
    __table_args__ = {
        "timescaledb_hypertable": {"time_column_name": "timestamp"}
    }
    
    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    robot_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("robots.id"))
    sensor_type: Mapped[str] = mapped_column(String(50))
    data: Mapped[dict] = mapped_column(JSONB)           # JSON形式で柔軟に保存
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"
    
    id: Mapped[UUID] = mapped_column(PG_UUID, primary_key=True)
    document_id: Mapped[UUID] = mapped_column(PG_UUID, ForeignKey("rag_documents.id"))
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(768))  # pgvector: 768次元ベクトル
    chunk_index: Mapped[int] = mapped_column(Integer)
```

---

## 5. Go ゲートウェイ

### 5.1 Go の基礎

```go
// Go はシンプルさを重視した言語

// ── パッケージ宣言 ──
package main  // 実行可能プログラムは必ず package main

// ── インポート ──
import (
    "fmt"       // 標準出力
    "net/http"  // HTTPサーバー
    "sync"      // 並行処理の同期
)

// ── 構造体（データの型）──
type Robot struct {
    ID     string  // 大文字始まり = 外部公開（public）
    Name   string
    speed  float64 // 小文字始まり = 内部のみ（private）
}

// ── メソッド ──
func (r *Robot) Move(linear, angular float64) error {
    // *Robot = ポインタレシーバ（元のデータを変更できる）
    r.speed = linear
    return nil
}

// ── インターフェース ──
type RobotAdapter interface {
    Connect(id string) error
    SendCommand(cmd Command) error
    EmergencyStop() error
}
// Go のインターフェースは「暗黙的に実装」
// メソッドが全て揃っていれば自動でインターフェースを満たす

// ── goroutine（軽量スレッド）──
go func() {
    // 別スレッドで並行実行される
    for data := range sensorChannel {
        processSensor(data)
    }
}()
```

### 5.2 Gateway メインプログラム

```go
// cmd/gateway/main.go

func main() {
    // 1. 設定読み込み
    cfg, err := config.Load()
    if err != nil {
        os.Exit(1)
    }
    
    // 2. ロガー初期化
    logger := initLogger(cfg.Logging.Level)
    
    // 3. Redis パブリッシャー初期化
    redisPublisher, err := bridge.NewRedisPublisher(cfg.Redis.URL, logger)
    
    // 4. アダプタレジストリ初期化
    registry := adapter.NewRegistry(logger)
    registry.RegisterFactory("mock", mock.Factory)
    
    // 5. 安全機能初期化
    estop := safety.NewEStopManager(logger)
    velLimiter := safety.NewVelocityLimiter(cfg.Safety.MaxLinearVelocity, ...)
    watchdog := safety.NewTimeoutWatchdog(cfg.Safety.CommandTimeout, ...)
    opLock := safety.NewOperationLock(cfg.Safety.OperationLockTimeout, logger)
    
    // 6. WebSocket Hub（接続管理）
    codec := protocol.NewCodec()
    hub := server.NewHub(logger)
    handler := server.NewHandler(hub, registry, estop, velLimiter, ...)
    
    // 7. HTTPサーバー起動
    mux := http.NewServeMux()
    mux.HandleFunc("/ws", handler.HandleWebSocket)
    mux.HandleFunc("/health", handler.HandleHealth)
    
    srv := &http.Server{Addr: ":8080", Handler: mux}
    go srv.ListenAndServe()
    
    // 8. グレースフルシャットダウン
    // Ctrl+C や kill シグナルを受け取ったら安全に停止
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit  // シグナルが来るまでブロック
    
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    srv.Shutdown(ctx)
}
```

### 5.3 安全機能

```go
// internal/safety/estop.go — 緊急停止マネージャー

type EStopManager struct {
    mu       sync.RWMutex          // 読み書きロック
    stopped  map[string]bool       // ロボットごとの停止状態
    globalStop bool                // 全体停止フラグ
    logger   *zap.Logger
}

func (m *EStopManager) Activate(robotID string) {
    m.mu.Lock()               // 書き込みロック取得
    defer m.mu.Unlock()       // 関数終了時に自動解放
    m.stopped[robotID] = true
    m.logger.Warn("E-Stop activated", zap.String("robot_id", robotID))
}

func (m *EStopManager) IsActive(robotID string) bool {
    m.mu.RLock()              // 読み取りロック（複数同時読み取り可）
    defer m.mu.RUnlock()
    if m.globalStop {
        return true
    }
    return m.stopped[robotID]
}


// internal/safety/velocity_limiter.go — 速度制限

type VelocityLimiter struct {
    maxLinear  float64  // 最大並進速度 (m/s)
    maxAngular float64  // 最大回転速度 (rad/s)
}

func (v *VelocityLimiter) Limit(linear, angular float64) (float64, float64) {
    // ベクトルの大きさで制限（方向を保持）
    mag := math.Sqrt(linear*linear + angular*angular)
    if mag > v.maxLinear {
        scale := v.maxLinear / mag
        linear *= scale
        angular *= scale
    }
    return linear, angular
}
```

### 5.4 WebSocket Hub パターン

```go
// internal/server/hub.go

type Hub struct {
    clients    map[string]*Client       // 接続中クライアント
    register   chan *Client              // 登録チャネル
    unregister chan *Client              // 登録解除チャネル
    mu         sync.RWMutex
}

func (h *Hub) Run() {
    for {
        select {
        case client := <-h.register:     // 新しい接続
            h.mu.Lock()
            h.clients[client.ID] = client
            h.mu.Unlock()

        case client := <-h.unregister:   // 切断
            h.mu.Lock()
            delete(h.clients, client.ID)
            h.mu.Unlock()
        }
    }
}

// 特定のロボットを購読しているクライアントにだけ送信
func (h *Hub) BroadcastToRobot(robotID string, msg []byte) {
    h.mu.RLock()
    defer h.mu.RUnlock()
    for _, client := range h.clients {
        if client.RobotID == robotID {
            client.Send <- msg  // チャネル経由で送信
        }
    }
}
```

### 5.5 モックアダプタ（シミュレーション）

```go
// internal/adapter/mock/mock_adapter.go

type MockAdapter struct {
    sensorCh chan *protocol.SensorData
    // ... 各センサーのシミュレーション用変数
}

func (m *MockAdapter) startSensorSimulation() {
    // オドメトリ: 20Hz（1秒に20回）
    go func() {
        ticker := time.NewTicker(50 * time.Millisecond)
        for range ticker.C {
            m.sensorCh <- &protocol.SensorData{
                Type: "odometry",
                Data: map[string]interface{}{
                    "x": m.posX, "y": m.posY, "theta": m.theta,
                },
            }
        }
    }()

    // LiDAR: 10Hz
    go func() {
        ticker := time.NewTicker(100 * time.Millisecond)
        for range ticker.C {
            ranges := m.simulateLiDAR()  // 360度のレーザースキャン
            m.sensorCh <- &protocol.SensorData{
                Type: "lidar",
                Data: map[string]interface{}{"ranges": ranges},
            }
        }
    }()
}
```

---

## 6. データベース (PostgreSQL)

### 6.1 使用技術

| 技術 | 用途 |
|------|------|
| **PostgreSQL 16** | メインDB |
| **TimescaleDB** | 時系列データの高速処理 |
| **pgvector** | AIベクトル検索（RAG用） |
| **SQLAlchemy 2.0** | PythonからDBを操作するORM |
| **Alembic** | DBスキーマの変更管理 |

### 6.2 テーブル構成

```sql
-- ユーザーテーブル
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ロボットテーブル
CREATE TABLE robots (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    adapter_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'idle',
    owner_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- センサーデータ（TimescaleDB ハイパーテーブル）
CREATE TABLE sensor_data (
    id UUID,
    robot_id UUID REFERENCES robots(id),
    sensor_type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,              -- 柔軟なJSON形式
    timestamp TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (id, timestamp)       -- 時間でパーティション
);
-- TimescaleDB: 自動的に時間で分割して高速化
SELECT create_hypertable('sensor_data', 'timestamp');

-- RAG ドキュメントチャンク（pgvectorでベクトル検索）
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES rag_documents(id),
    content TEXT NOT NULL,
    embedding VECTOR(768),            -- 768次元のベクトル
    chunk_index INTEGER NOT NULL
);
-- HNSW インデックス: ベクトル類似検索を高速化
CREATE INDEX ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
```

### 6.3 TimescaleDB クエリ例

```python
# infrastructure/database/repositories/sensor_data_repo.py

async def get_aggregated(
    self, robot_id: UUID, sensor_type: str,
    interval: str = "1 minute",
    start: datetime, end: datetime,
) -> list[dict]:
    """時間集約クエリ（例: 1分ごとの平均値）"""
    stmt = text("""
        SELECT
            time_bucket(:interval, timestamp) AS bucket,
            avg((data->>'value')::float) AS avg_value,
            min((data->>'value')::float) AS min_value,
            max((data->>'value')::float) AS max_value,
            count(*) AS sample_count
        FROM sensor_data
        WHERE robot_id = :robot_id
          AND sensor_type = :sensor_type
          AND timestamp BETWEEN :start AND :end
        GROUP BY bucket
        ORDER BY bucket
    """)
    # time_bucket: TimescaleDB独自の関数
    # 大量のセンサーデータを効率的に集約できる
```

### 6.4 pgvector 類似検索

```python
# infrastructure/database/repositories/rag_repo.py

async def search_similar_chunks(
    self, embedding: list[float],
    limit: int = 5,
    min_similarity: float = 0.7
) -> list[tuple[DocumentChunk, float]]:
    """ベクトル類似度でドキュメントを検索"""
    stmt = text("""
        SELECT *,
               1 - (embedding <=> :embedding::vector) AS similarity
        FROM document_chunks
        WHERE embedding IS NOT NULL
          AND 1 - (embedding <=> :embedding::vector) >= :min_similarity
        ORDER BY embedding <=> :embedding::vector
        LIMIT :limit
    """)
    # <=> はコサイン距離演算子（pgvector）
    # 値が小さいほど類似度が高い
    # 1 - distance = similarity（0〜1の類似度）
```


---

## 7. Protocol Buffers

### 7.1 Protocol Buffers とは？

Protocol Buffers (protobuf) は Google が開発した、データを効率的にやり取りするための仕組みです。JSONよりコンパクトで高速です。

```protobuf
// proto/sensor.proto

syntax = "proto3";   // バージョン3を使用
package robotai;     // 名前空間

// ── センサーデータの定義 ──
message LaserScan {
  float angle_min = 1;           // フィールド番号（順序ではなくID）
  float angle_max = 2;
  float angle_increment = 3;
  repeated float ranges = 4;     // repeated = 配列
  repeated float intensities = 5;
}

message Odometry {
  double x = 1;
  double y = 2;
  double theta = 3;              // 向き（ラジアン）
  double linear_velocity = 4;
  double angular_velocity = 5;
}

message BatteryState {
  float voltage = 1;
  float percentage = 2;
  string status = 3;             // "charging", "discharging"
}

// ── oneof: いずれか一つのデータを持つ ──
message SensorData {
  string robot_id = 1;
  int64 timestamp = 2;
  oneof data {                   // この中の一つだけが入る
    LaserScan laser_scan = 10;
    Odometry odometry = 11;
    Imu imu = 12;
    BatteryState battery = 13;
    CompressedImage image = 14;
  }
}
```

```protobuf
// proto/command.proto

message VelocityCommand {
  double linear_x = 1;          // 前進速度 (m/s)
  double angular_z = 2;         // 回転速度 (rad/s)
}

message NavigationGoal {
  double x = 1;                 // 目標X座標
  double y = 2;                 // 目標Y座標
  double theta = 3;             // 目標向き
}

message EmergencyStop {
  bool activate = 1;            // true=停止, false=解除
  string reason = 2;            // 理由
}

// ── ロボットへのコマンド ──
message RobotCommand {
  string robot_id = 1;
  oneof command {
    VelocityCommand velocity = 10;
    NavigationGoal nav_goal = 11;
    EmergencyStop estop = 12;
  }
}
```

```protobuf
// proto/gateway_service.proto

// ── gRPC サービス定義 ──
service GatewayService {
  rpc SendCommand(RobotCommand) returns (CommandResponse);
  rpc GetRobotStatus(RobotStatusRequest) returns (RobotStatus);
  rpc StreamSensorData(SensorStreamRequest) returns (stream SensorData);
  // stream = サーバーからデータが連続で送られる
}
```

**初心者ポイント**: protobuf はデータの形（スキーマ）を定義するだけ。実際のコードは自動生成される。

---

## 8. デザインパターン

### 8.1 クリーンアーキテクチャ（バックエンド）

```
          ┌─────────────────────────────────┐
          │         API Layer               │  ← HTTPリクエスト受付
          │  (endpoints, schemas)           │
          └──────────────┬──────────────────┘
                         │ 依存
          ┌──────────────▼──────────────────┐
          │       Domain Layer              │  ← ビジネスルール
          │  (entities, repositories,       │     （外部に依存しない）
          │   services)                     │
          └──────────────┬──────────────────┘
                         │ 実装
          ┌──────────────▼──────────────────┐
          │    Infrastructure Layer         │  ← 外部接続
          │  (database, redis, llm)         │     （DBやAPIの具体実装）
          └─────────────────────────────────┘
```

**ポイント**: Domain層は「抽象クラス (ABC)」でインターフェースだけ定義し、Infrastructure層で具体的に実装する。これにより、DBの種類を変えてもビジネスロジックに影響しない。

### 8.2 アダプタパターン（ゲートウェイ）

```go
// ── 抽象インターフェース ──
type RobotAdapter interface {
    Connect(robotID string) error
    Disconnect() error
    SendCommand(cmd Command) error
    SensorDataChannel() <-chan *SensorData
    EmergencyStop() error
}

// ── ファクトリ関数 ──
type AdapterFactory func(config map[string]interface{}, logger *zap.Logger) (RobotAdapter, error)

// ── レジストリ（工場の登録簿）──
type Registry struct {
    factories map[string]AdapterFactory  // "mock" → MockAdapterを作る関数
    mu        sync.RWMutex
}

func (r *Registry) RegisterFactory(name string, factory AdapterFactory) {
    r.mu.Lock()
    defer r.mu.Unlock()
    r.factories[name] = factory
}

func (r *Registry) Create(name string, config map[string]interface{}) (RobotAdapter, error) {
    r.mu.RLock()
    factory, ok := r.factories[name]
    r.mu.RUnlock()
    if !ok {
        return nil, fmt.Errorf("unknown adapter: %s", name)
    }
    return factory(config, r.logger)
}
```

**使い方**:
```go
// "mock" アダプタを作成（将来 "ros2", "grpc" なども追加可能）
adapter, err := registry.Create("mock", config)
adapter.Connect("robot-1")
```

### 8.3 リポジトリパターン（バックエンド）

```python
# ── 抽象リポジトリ ──
class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, id: UUID) -> T | None: ...
    
    @abstractmethod
    async def create(self, entity: T) -> T: ...
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool: ...

# ── 具体的な実装 ──
class SQLAlchemyUserRepository(UserRepository):
    # PostgreSQL用の実装
    ...

# ── テスト用の実装（将来）──
class InMemoryUserRepository(UserRepository):
    # メモリ上のdict で実装（テスト時に使う）
    ...
```

### 8.4 Hub パターン（ゲートウェイ）

WebSocket の接続管理に使われるパターンです。

```
  Client A ──┐
  Client B ──┤──► Hub ──► BroadcastToRobot("robot-1")
  Client C ──┘        ├── Client A (robot-1を購読) ← 受信
                      ├── Client B (robot-2を購読) ← 受信しない
                      └── Client C (robot-1を購読) ← 受信
```

### 8.5 Zustand ストアパターン（フロントエンド）

```typescript
// ── グローバル状態管理 ──
// Redux と違い、ボイラープレート（定型コード）が少ない

// stores/robotStore.ts
import { create } from "zustand";

interface RobotState {
  selectedRobotId: string | null;
  sensorData: Record<string, SensorData>;
  isEstopped: boolean;

  selectRobot: (id: string) => void;
  updateSensor: (type: string, data: SensorData) => void;
  setEstop: (active: boolean) => void;
}

export const useRobotStore = create<RobotState>()((set) => ({
  selectedRobotId: null,
  sensorData: {},
  isEstopped: false,

  selectRobot: (id) => set({ selectedRobotId: id }),
  
  updateSensor: (type, data) =>
    set((state) => ({
      sensorData: { ...state.sensorData, [type]: data },
      // スプレッド構文: 既存データをコピーして一部を上書き
    })),
  
  setEstop: (active) => set({ isEstopped: active }),
}));
```

---

## 9. セキュリティ

### 9.1 JWT 認証フロー

```
1. ログイン
   Client → POST /auth/login {email, password}
   Server → {access_token (15分), refresh_token (7日)}

2. API呼び出し
   Client → GET /robots  (Header: Authorization: Bearer <access_token>)
   Server → トークン検証 → ユーザー取得 → レスポンス

3. トークン更新（access_token 期限切れ時）
   Client → POST /auth/refresh {refresh_token}
   Server → 新しい {access_token, refresh_token}

4. 自動更新（Axios インターセプター）
   401エラー → 自動でリフレッシュ → 元のリクエストを再実行
```

### 9.2 パスワードハッシュ化

```python
# core/security.py

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """パスワードを不可逆にハッシュ化"""
    return pwd_context.hash(password)
    # "password123" → "$2b$12$LJ3..." （元に戻せない）

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """入力パスワードとハッシュを比較"""
    return pwd_context.verify(plain_password, hashed_password)
```

### 9.3 JWT トークン生成

```python
# core/security.py

from jose import jwt

def create_tokens(*, user_id: str, role: str) -> dict[str, str]:
    settings = get_settings()
    
    # RS256: 秘密鍵で署名、公開鍵で検証
    # → Gatewayは公開鍵だけでトークンの正当性を確認できる
    key = settings.jwt_private_key or settings.secret_key
    algorithm = "RS256" if settings.jwt_private_key else "HS256"
    
    access_payload = {
        "sub": user_id,        # subject（対象ユーザー）
        "role": role,          # 権限
        "exp": now + timedelta(minutes=15),  # 有効期限
        "type": "access",
    }
    
    return {
        "access_token": jwt.encode(access_payload, key, algorithm=algorithm),
        "refresh_token": jwt.encode(refresh_payload, key, algorithm=algorithm),
    }
```

### 9.4 RBAC (役割ベースアクセス制御)

```
┌──────────┬─────────────────────────────────────┐
│  Role    │ 許可される操作                       │
├──────────┼─────────────────────────────────────┤
│ admin    │ すべて（ユーザー管理、ロボット操作） │
│ operator │ ロボット操作、データ閲覧            │
│ viewer   │ データ閲覧のみ                      │
└──────────┴─────────────────────────────────────┘
```

```python
# 使用例: admin権限が必要なエンドポイント
@router.delete("/{robot_id}")
async def delete_robot(user: AdminUser, ...):
    # AdminUser = require_role(UserRole.ADMIN) で保護
    ...
```

---

## 10. Docker / インフラ

### 10.1 Docker の基本概念

```
Docker コンテナ = アプリとその実行環境をまとめたパッケージ

    ┌────────────────────────────────────────────┐
    │           Docker Compose                    │
    │                                             │
    │  ┌──────┐ ┌──────┐ ┌───────┐ ┌──────────┐  │
    │  │Front │ │Back  │ │Gateway│ │PostgreSQL│  │
    │  │end   │ │end   │ │      │ │+Timescale│  │
    │  └──────┘ └──────┘ └───────┘ └──────────┘  │
    │  ┌──────┐ ┌──────┐                          │
    │  │Redis │ │Ollama│                          │
    │  └──────┘ └──────┘                          │
    └────────────────────────────────────────────┘
```

### 10.2 Dockerfile の読み方

```dockerfile
# backend/Dockerfile — マルチステージビルド

# ── ステージ1: ビルド ──
FROM python:3.12-slim AS builder  # ベースイメージ
WORKDIR /app                      # 作業ディレクトリ
COPY pyproject.toml .             # 依存関係定義をコピー
COPY app/ ./app/                  # ソースコードをコピー
RUN pip install --no-cache-dir --prefix=/install .  # インストール

# ── ステージ2: 実行 ──
FROM python:3.12-slim AS runtime  # 小さいイメージで再スタート
RUN groupadd -r appuser && useradd -r -g appuser appuser  # 専用ユーザー
WORKDIR /app
COPY --from=builder /install /usr/local  # ビルド結果だけコピー
COPY . .
USER appuser                      # root以外で実行（セキュリティ）
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# gateway/Dockerfile — Go のビルド

FROM golang:1.22-alpine AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download             # 依存関係のダウンロード
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o gateway ./cmd/gateway/
# CGO_ENABLED=0: C言語依存なし（静的リンク）
# -ldflags="-w -s": デバッグ情報を削除（実行ファイルを小さく）

FROM gcr.io/distroless/static-debian12  # 最小イメージ（シェルすらない）
COPY --from=builder /build/gateway /app/gateway
USER nonroot:nonroot
ENTRYPOINT ["/app/gateway"]
```

### 10.3 Docker Compose

```yaml
# docker-compose.yml（基本構成）

services:
  frontend:
    build: ./frontend
    depends_on:
      backend: { condition: service_healthy }  # backendが健全になるまで待機

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://...    # 環境変数で設定注入
      - REDIS_URL=redis://:password@redis:6379/0
    volumes:
      - ./keys:/app/keys:ro          # :ro = 読み取り専用マウント
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health')"]
      interval: 10s
      retries: 5

  postgres:
    image: timescale/timescaledb:latest-pg16  # 既成イメージを使用
    volumes:
      - postgres-data:/var/lib/postgresql/data  # データ永続化

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    # appendonly yes: データを永続化

  ollama:
    image: ollama/ollama:latest       # ローカルLLM
    volumes:
      - ollama-data:/root/.ollama     # モデルデータ永続化

networks:
  frontend-network: {}   # フロントエンドとバックエンドの通信
  backend-network: {}    # バックエンドとDB/Redisの通信

volumes:
  postgres-data: {}      # 名前付きボリューム
  redis-data: {}
  ollama-data: {}
```

### 10.4 開発 vs 本番の違い

```yaml
# docker-compose.dev.yml（開発用オーバーレイ）
services:
  frontend:
    volumes:
      - ./frontend/src:/app/src      # ソースコードをマウント
    command: npm run dev -- --host 0.0.0.0  # ホットリロード有効

  backend:
    command: uvicorn app.main:app --reload  # コード変更で自動再起動
    
  postgres:
    ports: ["15432:5432"]            # 外部からDB接続可能

# docker-compose.prod.yml（本番用オーバーレイ）
services:
  backend:
    command: gunicorn app.main:app --workers 4  # 複数ワーカーで高負荷対応
    deploy:
      resources:
        limits: { memory: 1G, cpus: "2.0" }    # リソース制限

  postgres:
    ports: []                        # 外部接続を遮断
    command: >
      postgres -c shared_buffers=512MB         # チューニング設定
```

---

## 11. CI/CD

### 11.1 CI/CD とは？

```
CI (Continuous Integration): コードを変更するたびに自動テスト
CD (Continuous Deployment): テスト通過後に自動デプロイ

  コード変更 → テスト → ビルド → デプロイ
  (自動)      (自動)   (自動)   (自動)
```

### 11.2 GitHub Actions ワークフロー

```yaml
# .github/workflows/ci.yml — テスト・ビルド

name: CI Pipeline
on:
  push:
    branches: [main, develop]     # main/developへのpushで実行
  pull_request:
    branches: [main]              # mainへのPRで実行

jobs:
  # ── バックエンドのテスト ──
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:                   # テスト用DBを自動起動
        image: timescale/timescaledb:latest-pg16
        env:
          POSTGRES_PASSWORD: test
    steps:
      - uses: actions/checkout@v4        # コード取得
      - uses: actions/setup-python@v5    # Python環境構築
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev]"     # 依存関係インストール
      - run: pytest --cov                # テスト実行＋カバレッジ

  # ── フロントエンドのテスト ──
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci                      # 依存関係インストール
      - run: npm run lint                # コードスタイルチェック
      - run: npm test                    # テスト実行
      - run: npm run build               # ビルド確認

  # ── ゲートウェイのテスト ──
  gateway-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with: { go-version: "1.22" }
      - run: go test ./...               # 全パッケージテスト
      - run: go vet ./...                # 静的解析
      - run: go build ./cmd/gateway/     # ビルド確認
```

```yaml
# .github/workflows/cd-production.yml — 本番デプロイ

name: CD Production
on:
  push:
    tags: ["v*"]                  # v1.0.0 のようなタグで発火

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Docker イメージをビルドしてレジストリにプッシュ
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            ghcr.io/org/backend:latest
            ghcr.io/org/backend:${{ github.ref_name }}
```


---

## 12. WebSocket リアルタイム通信

### 12.1 通信の全体像

```
ブラウザ (React)
    │
    │ WebSocket接続
    │ ws://localhost:8080/ws?robot_id=xxx&token=yyy
    │
    ▼
Gateway (Go)
    │
    ├── 認証: トークン検証
    ├── Hub: クライアント管理
    ├── Handler: メッセージルーティング
    ├── Safety: 安全チェック
    │
    │ Redis Streams
    ▼
Backend (Python)
    │
    ├── RecordingWorker: データ記録
    └── Database: 永続化
```

### 12.2 メッセージ形式

```go
// internal/protocol/messages.go

type Message struct {
    Type      string      `json:"type"`       // メッセージ種別
    Payload   interface{} `json:"payload"`    // データ本体
    RobotID   string      `json:"robot_id"`   // 対象ロボット
    Timestamp int64       `json:"timestamp"`  // タイムスタンプ
    RequestID string      `json:"request_id"` // リクエスト追跡用
}

// メッセージ種別の例:
// Client → Gateway:
//   "velocity_cmd"  - 速度コマンド
//   "estop"         - 緊急停止
//   "nav_goal"      - ナビゲーション目標
//   "ping"          - 生存確認
//
// Gateway → Client:
//   "sensor_data"   - センサーデータ
//   "robot_status"  - ロボット状態
//   "estop_status"  - 緊急停止状態
//   "pong"          - ping応答
//   "error"         - エラー通知
```

### 12.3 メッセージ処理

```go
// internal/server/handler.go

func (h *Handler) HandleMessage(client *Client, msg *protocol.Message) {
    switch msg.Type {
    case "velocity_cmd":
        // 1. 緊急停止中か確認
        if h.estop.IsActive(msg.RobotID) {
            client.SendError("E-Stop is active")
            return
        }
        // 2. 操作ロック確認
        if !h.opLock.HasLock(msg.RobotID, client.UserID) {
            client.SendError("Operation lock not held")
            return
        }
        // 3. 速度制限を適用
        limited := h.velLimiter.Limit(cmd.LinearX, cmd.AngularZ)
        // 4. ウォッチドッグをリセット
        h.watchdog.Reset(msg.RobotID)
        // 5. アダプタ経由でロボットに送信
        adapter.SendCommand(limited)
        // 6. Redis にも記録
        h.redis.PublishCommand(msg)

    case "estop":
        h.estop.Activate(msg.RobotID)
        h.hub.BroadcastToRobot(msg.RobotID, estopMsg)

    case "ping":
        client.Send(pongMessage)
    }
}
```

### 12.4 Redis Streams 連携

```go
// internal/bridge/redis_publisher.go

type RedisPublisher struct {
    client *redis.Client
}

func (p *RedisPublisher) PublishSensorData(robotID string, data *protocol.SensorData) error {
    return p.client.XAdd(ctx, &redis.XAddArgs{
        Stream: "robot:sensor_data",    // ストリーム名
        Values: map[string]interface{}{
            "robot_id":    robotID,
            "sensor_type": data.Type,
            "data":        jsonBytes,   // JSON形式のデータ
        },
    }).Err()
}
```

```python
# backend — RecordingWorker がRedis Streamsを購読

class RecordingWorker:
    async def _run(self):
        while self._running:
            # xreadgroup: コンシューマグループでメッセージを読む
            results = await self._redis.xreadgroup(
                groupname="backend-workers",
                consumername="worker-1",
                streams={"robot:sensor_data": ">", "robot:commands": ">"},
                count=50,        # 一度に最大50件
                block=1000,      # 1秒待ってデータがなければリトライ
            )
            for stream_name, messages in results:
                for msg_id, fields in messages:
                    await self._process_message(stream_name, fields)
                    await self._redis.xack(stream_name, "backend-workers", msg_id)
                    # xack: 処理完了を通知（再送防止）
```

---

## 13. RAG (検索拡張生成)

### 13.1 RAG とは？

```
RAG = Retrieval Augmented Generation（検索拡張生成）

通常のAI:
  質問 → LLM → 回答（学習データのみ）

RAG:
  質問 → 類似文書を検索 → 検索結果 + 質問 → LLM → 回答
          ↑ pgvectorで
          ベクトル類似検索
```

### 13.2 ドキュメントの取り込みフロー

```
1. PDF/テキストをアップロード
2. テキストを抽出
3. チャンクに分割（500文字ごと、100文字重複）
4. 各チャンクをベクトル化（nomic-embed-text → 768次元）
5. PostgreSQL の document_chunks テーブルに保存
```

```python
# domain/services/rag_service.py

class TextSplitter:
    """テキストをチャンクに分割"""
    def __init__(self, chunk_size=500, overlap=100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def split(self, text: str) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.overlap  # 重複ありで次のチャンクへ
        return chunks
```

### 13.3 質問応答フロー

```python
# domain/services/rag_service.py

class RAGService:
    async def query(self, question: str, top_k: int = 5) -> RAGQueryResult:
        # 1. 質問文をベクトル化
        question_embedding = await self.embedding.embed(question)
        
        # 2. 類似チャンクを検索（pgvector のコサイン類似度）
        results = await self.rag_repo.search_similar_chunks(
            embedding=question_embedding,
            limit=top_k,
            min_similarity=0.7,
        )
        
        # 3. コンテキストを構築
        context = "\n\n".join([
            f"[Source {i+1}] {chunk.content}"
            for i, (chunk, score) in enumerate(results)
        ])
        
        # 4. LLM に質問（コンテキスト付き）
        answer = await self.llm.generate(
            prompt=question,
            context=context,
        )
        
        return RAGQueryResult(
            answer=answer,
            sources=[...],
        )
```

### 13.4 Ollama LLM クライアント

```python
# infrastructure/llm/ollama_client.py

class OllamaClient:
    """ローカルLLM（Llama 3）との通信"""
    
    async def generate(self, prompt: str, context: str = "") -> str:
        system_prompt = (
            "You are a helpful robot AI assistant..."
        )
        if context:
            system_prompt += f"\n\nContext:\n{context}"
        
        response = await self._client.post(
            "/api/chat",
            json={
                "model": "llama3",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
        )
        return response.json()["message"]["content"]
    
    async def generate_stream(self, prompt, context=""):
        """ストリーミング応答（トークンが一つずつ返る）"""
        async with self._client.stream("POST", "/api/chat", json=...) as response:
            async for line in response.aiter_lines():
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content  # 1トークンずつ返す
```

### 13.5 Embedding サービス

```python
# infrastructure/llm/embedding.py

class EmbeddingService:
    """テキスト → 768次元ベクトルに変換"""
    
    async def embed(self, text: str) -> list[float]:
        response = await self._client.post(
            "/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text},
        )
        return response.json()["embedding"]
        # 返り値: [0.123, -0.456, 0.789, ...] (768個の数値)
```

---

## 14. 安全機能

### 14.1 安全機能一覧

| 機能 | 説明 | ファイル |
|------|------|----------|
| **E-Stop** | 緊急停止（即座に全停止） | `safety/estop.go` |
| **速度制限** | 最大速度を制限 | `safety/velocity_limiter.go` |
| **タイムアウト監視** | コマンド途絶時に自動停止 | `safety/timeout_watchdog.go` |
| **操作ロック** | 1人だけが操作可能 | `safety/operation_lock.go` |

### 14.2 操作ロック

```go
// safety/operation_lock.go

type OperationLock struct {
    locks   map[string]*lockInfo  // robotID → ロック情報
    timeout time.Duration         // ロックの有効期限
    mu      sync.RWMutex
}

type lockInfo struct {
    UserID    string
    ExpiresAt time.Time
}

func (o *OperationLock) Acquire(robotID, userID string) bool {
    o.mu.Lock()
    defer o.mu.Unlock()
    
    // 既存ロックの確認
    if existing, ok := o.locks[robotID]; ok {
        if time.Now().Before(existing.ExpiresAt) && existing.UserID != userID {
            return false  // 他のユーザーがロック中
        }
    }
    
    o.locks[robotID] = &lockInfo{
        UserID:    userID,
        ExpiresAt: time.Now().Add(o.timeout),  // 5分後に自動解放
    }
    return true
}
```

### 14.3 タイムアウト監視

```go
// safety/timeout_watchdog.go

type TimeoutWatchdog struct {
    timers  map[string]*time.Timer  // robotID → タイマー
    timeout time.Duration           // コマンドの有効期限（3秒）
    onTimeout func(robotID string)  // タイムアウト時のコールバック
}

func (w *TimeoutWatchdog) Reset(robotID string) {
    // コマンドを受信するたびにタイマーをリセット
    if timer, ok := w.timers[robotID]; ok {
        timer.Stop()
    }
    w.timers[robotID] = time.AfterFunc(w.timeout, func() {
        // 3秒間コマンドが来なかったら自動停止
        w.onTimeout(robotID)
    })
}
```

### 14.4 フロントエンドの緊急停止ボタン

```tsx
// components/control/EStopButton.tsx

export function EStopButton() {
  const { isEstopped } = useRobotStore();
  const { sendCommand } = useWebSocket(robotId);

  return (
    <button
      onClick={() => sendCommand("estop", {
        activate: !isEstopped,
        reason: "operator_request"
      })}
      className={cn(
        "w-24 h-24 rounded-full font-bold text-white text-xl",
        "border-4 shadow-lg transition-all",
        isEstopped
          ? "bg-yellow-600 border-yellow-400"          // 解除可能状態
          : "bg-red-600 border-red-400 animate-estop-pulse" // 待機中
      )}
    >
      {isEstopped ? "RESET" : "E-STOP"}
    </button>
  );
}
```

---

## 15. テスト

### 15.1 テスト構成

```
backend/tests/
├── conftest.py              # pytest 共通設定
├── test_auth.py             # 認証テスト
├── test_robots.py           # ロボットCRUDテスト
└── test_sensors.py          # センサーデータテスト

frontend/src/
├── __tests__/               # Vitest テスト
└── *.test.tsx               # コンポーネントテスト

gateway/
└── *_test.go                # Go テスト
```

### 15.2 バックエンドテスト例

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient

@pytest.fixture
async def client():
    """テスト用HTTPクライアント"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# tests/test_auth.py
async def test_login_success(client):
    """正常なログインテスト"""
    response = await client.post("/api/v1/auth/login", json={
        "username": "admin@example.com",
        "password": "testpass",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

async def test_login_invalid_password(client):
    """不正なパスワードのテスト"""
    response = await client.post("/api/v1/auth/login", json={
        "username": "admin@example.com",
        "password": "wrong",
    })
    assert response.status_code == 401
```

### 15.3 フロントエンドテスト例

```typescript
// __tests__/LoginPage.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { LoginPage } from "../pages/LoginPage";

test("ログインフォームが表示される", () => {
  render(<LoginPage />);
  expect(screen.getByLabelText("Email")).toBeInTheDocument();
  expect(screen.getByLabelText("Password")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /ログイン/ })).toBeInTheDocument();
});
```

### 15.4 Go テスト例

```go
// internal/safety/estop_test.go
func TestEStopActivateAndDeactivate(t *testing.T) {
    logger, _ := zap.NewDevelopment()
    estop := NewEStopManager(logger)

    // 初期状態: 停止していない
    if estop.IsActive("robot-1") {
        t.Error("expected not active")
    }

    // 緊急停止を有効化
    estop.Activate("robot-1")
    if !estop.IsActive("robot-1") {
        t.Error("expected active")
    }

    // 解除
    estop.Deactivate("robot-1")
    if estop.IsActive("robot-1") {
        t.Error("expected deactivated")
    }
}
```

---

## 16. 用語集

| 用語 | 英語 | 説明 |
|------|------|------|
| API | Application Programming Interface | ソフトウェア間の通信の取り決め |
| REST | Representational State Transfer | Web APIの設計スタイル（GET, POST, PUT, DELETE） |
| JWT | JSON Web Token | 認証用の暗号化トークン |
| WebSocket | - | サーバーとクライアント間の双方向リアルタイム通信 |
| ORM | Object-Relational Mapping | プログラムのオブジェクトとDBテーブルの相互変換 |
| DI | Dependency Injection | 依存性注入。必要な部品を外から渡す設計 |
| RBAC | Role-Based Access Control | 役割に基づくアクセス制御 |
| gRPC | Google Remote Procedure Call | 高速なサービス間通信プロトコル |
| Docker | - | アプリを隔離環境（コンテナ）で実行する技術 |
| CI/CD | Continuous Integration/Deployment | 自動テスト・自動デプロイ |
| RAG | Retrieval Augmented Generation | 検索結果でAIの回答を強化する手法 |
| LLM | Large Language Model | ChatGPTのような大規模言語モデル |
| E-Stop | Emergency Stop | 緊急停止 |
| TimescaleDB | - | 時系列データ用PostgreSQL拡張 |
| pgvector | - | ベクトル検索用PostgreSQL拡張 |
| Zustand | - | React用の軽量状態管理ライブラリ |
| Axios | - | HTTPクライアントライブラリ |
| FastAPI | - | Python用の高速Webフレームワーク |
| SQLAlchemy | - | PythonのORM/DBツールキット |
| goroutine | - | Goの軽量並行処理単位 |
| channel | - | goroutine間でデータを受け渡す仕組み |
| Mutex | Mutual Exclusion | 排他制御。複数スレッドの同時アクセスを防ぐ |
| Redis Streams | - | メッセージキュー機能を持つRedisのデータ構造 |
| Protocol Buffers | protobuf | 効率的なデータシリアライズ形式 |
| HNSW | Hierarchical Navigable Small World | 高速近似最近傍探索アルゴリズム |
| SSE | Server-Sent Events | サーバーからクライアントへの単方向ストリーミング |

---

## 付録: よく使うコマンド

```bash
# ── 開発環境の起動 ──
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# ── ログの確認 ──
docker compose logs -f backend    # バックエンドのログ
docker compose logs -f gateway    # ゲートウェイのログ

# ── データベースに接続 ──
docker compose exec postgres psql -U robot_app -d robot_ai_db

# ── テスト実行 ──
cd backend && pytest --cov                    # Python テスト
cd frontend && npm test                       # React テスト
cd gateway && go test ./...                   # Go テスト

# ── Ollama にモデルをダウンロード ──
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull nomic-embed-text

# ── RSA鍵ペアの生成（JWT用）──
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem

# ── 本番ビルド・起動 ──
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

> **学習のアドバイス**: このガイドは全体像を掴むためのものです。まずは以下の順序で学ぶことをお勧めします:
> 1. TypeScript の基本構文 → React のコンポーネント → `LoginPage.tsx` を読む
> 2. Python の基本 → FastAPI の公式チュートリアル → `endpoints/auth.py` を読む
> 3. Docker Compose で環境を起動し、実際にアプリを動かしてみる
> 4. 各ファイルを少しずつ変更して動作の変化を観察する
