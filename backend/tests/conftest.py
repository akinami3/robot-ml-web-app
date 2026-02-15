"""
=============================================================================
テスト設定ファイル（conftest.py）
=============================================================================

【conftest.py とは？】
pytestが自動的に読み込む特別な設定ファイルです。
このファイルに定義した「フィクスチャ（fixture）」は、
同じディレクトリとサブディレクトリのすべてのテストファイルから使用できます。

【フィクスチャ（fixture）とは？】
テストの「前準備」を行う関数です。テストに必要なデータやオブジェクトを
用意して提供（inject = 注入）します。

例:
  @pytest.fixture
  def sample_user():
      return User(name="テスト太郎")

  def test_user_name(sample_user):  ← 引数名がフィクスチャ名と一致すると自動注入
      assert sample_user.name == "テスト太郎"

【なぜフィクスチャを使う？】
  - テストデータの準備コードを共通化（DRY原則: 繰り返しを避ける）
  - テスト本体をシンプルに保てる
  - 後片付け（クリーンアップ）も自動化できる（yield を使用）
=============================================================================
"""

# 【__future__ annotations】Python 3.10以降の型ヒント記法をそれ以前でも使えるようにする
# 例: list[str] や int | None のような簡潔な書き方が可能になる
from __future__ import annotations

# 【asyncio】非同期処理ライブラリ（非同期テストで使用）
import asyncio

# 【datetime】日付・時刻を扱うライブラリ
from datetime import datetime

# 【AsyncGenerator】非同期ジェネレータの型ヒント
# 非同期でデータを順次返す関数の戻り値型として使用
from typing import AsyncGenerator

# 【uuid4】一意なID（UUID = Universally Unique Identifier）を生成
# ランダムな128ビットの識別子（例: "550e8400-e29b-41d4-a716-446655440000"）
from uuid import uuid4

# 【pytest】Pythonのテストフレームワーク
import pytest

# 【pytest_asyncio】非同期テスト用のpytestプラグイン
# 非同期のフィクスチャや非同期テスト関数をサポートする
import pytest_asyncio

# 【ASGITransport】ASGI（非同期Webアプリ）をテストするためのトランスポート層
# 実際のHTTPサーバーを起動せずに、アプリ内部で直接リクエストを処理する
# → テストが高速で、ポート占有の問題もない
from httpx import ASGITransport, AsyncClient

# 【アプリケーションの依存関係をインポート】
from app.config import Settings
from app.core.security import hash_password
from app.domain.entities.user import User, UserRole
from app.main import create_app


# =============================================================================
# イベントループのフィクスチャ
# =============================================================================
@pytest.fixture(scope="session")
def event_loop():
    """
    テストセッション全体で共有するイベントループを提供します。

    【イベントループとは？】
    非同期処理（async/await）を実行するための仕組みです。
    非同期タスクの順番を管理し、効率的に実行します。

    【scope="session"とは？】
    フィクスチャのスコープ（有効範囲）を指定します:
      "function" （デフォルト）: 各テスト関数ごとに新しいインスタンスを作成
      "class"   : テストクラスごとに1つ
      "module"  : テストファイルごとに1つ
      "session" : テスト全体で1つ（最も広い範囲）

    イベントループは重いリソースなので、session スコープで1つだけ作成し、
    すべてのテストで共有します。

    【yield とは？（フィクスチャでの使い方）】
    yield の前: テスト実行前の「セットアップ（前準備）」
    yield の値: テストに渡されるオブジェクト
    yield の後: テスト実行後の「ティアダウン（後片付け）」

    この例:
      loop = asyncio.new_event_loop()  ← セットアップ（ループ作成）
      yield loop                        ← テストにループを渡す
      loop.close()                      ← ティアダウン（ループを閉じる）
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# テスト用設定のフィクスチャ
# =============================================================================
@pytest.fixture
def settings() -> Settings:
    """
    テスト用のアプリケーション設定を提供します。

    【Settings】アプリケーション全体の設定を管理するオブジェクト
    テストでは本番とは異なる設定を使用します:
      - environment="test"     : テスト環境であることを示す
      - debug=True             : デバッグモード（詳細なエラー情報を表示）
      - database_url=sqlite... : テスト用の軽量DB（本番はPostgreSQLなど）
        aiosqlite: SQLiteの非同期ドライバ
      - redis_url=.../1        : Redis のデータベース番号1を使用（本番は0）
        → テストデータと本番データを分離
      - secret_key="test-..."  : テスト用のシークレットキー（本番では強力な値を使用）
      - cors_origins            : テスト用のフロントエンドURL

    【scope指定なし → "function" スコープ】
    各テスト関数ごとに新しい Settings が作成される
    → テスト間の設定汚染（前のテストの変更が次に影響）を防止
    """
    return Settings(
        environment="test",
        debug=True,
        database_url="sqlite+aiosqlite:///test.db",
        redis_url="redis://localhost:6379/1",
        secret_key="test-secret-key",
        jwt_algorithm="HS256",
        cors_origins="http://localhost:3000",
    )


# =============================================================================
# テスト用ユーザーのフィクスチャ
# =============================================================================
@pytest.fixture
def test_user() -> User:
    """
    一般テストユーザー（オペレーター権限）を提供します。

    【Arrange パターン】
    テストの「Arrange-Act-Assert」パターンの「Arrange（準備）」を
    フィクスチャで行います:
      Arrange: テストに必要なデータを準備（このフィクスチャ）
      Act:     テスト対象の操作を実行
      Assert:  結果が期待通りかを検証

    【uuid4()】テストごとにランダムなIDを生成
    → テスト間でのID衝突を防止

    【hash_password】パスワードをハッシュ化（暗号化）して保存
    セキュリティ上、パスワードを平文（そのまま）で保存してはいけない
    → ハッシュ化すると元のパスワードに戻すことができなくなる

    【UserRole.OPERATOR】オペレーター権限
    ロボットを操作できるが、ユーザー管理はできない中間的な権限
    """
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        role=UserRole.OPERATOR,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def admin_user() -> User:
    """
    管理者ユーザー（アドミン権限）を提供します。

    【UserRole.ADMIN】最高権限
    すべての操作が可能（ロボット操作 + ユーザー管理 + システム設定）

    【test_user との使い分け】
    - 権限チェックのテスト: admin_user でアクセスできることを確認
    - 権限制限のテスト: test_user（OPERATOR）でアクセスできないことを確認
    → 権限システムが正しく動作することを両面から検証
    """
    return User(
        id=uuid4(),
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# =============================================================================
# 非同期HTTPクライアントのフィクスチャ
# =============================================================================
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    テスト用の非同期HTTPクライアントを提供します。

    【@pytest_asyncio.fixture】
    非同期（async）のフィクスチャを定義するデコレータ。
    通常の @pytest.fixture は同期関数用、async 関数にはこちらを使います。

    【AsyncGenerator[AsyncClient, None]】
    型ヒントの意味:
      - AsyncGenerator: 非同期ジェネレータ（yieldを使う非同期関数）
      - AsyncClient: yield で返す型（テストに渡すオブジェクト）
      - None: ジェネレータに送信する型（使わないので None）

    【ASGITransport】
    ASGI（Asynchronous Server Gateway Interface）アプリを
    実際のサーバーを起動せずにテストできる仕組み。

    通常のHTTPリクエスト: ブラウザ → ネットワーク → サーバー → アプリ
    テスト用:           テストコード → ASGITransport → アプリ

    → ネットワーク通信なしで直接アプリにリクエストを送れる
    → テストが高速で安定（ネットワークエラーの心配がない）

    【AsyncClient】
    httpxライブラリの非同期HTTPクライアント。
    テスト内で client.get("/api/users") のように使用して、
    APIエンドポイントにリクエストを送信します。
    base_url="http://test" はダミーURL（実際にはネットワーク通信しない）

    【async with ~ as ac】
    非同期コンテキストマネージャ。接続の開始と終了を自動管理します。
    ブロック終了時にクライアントの接続リソースが自動的にクリーンアップされます。
    """
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
