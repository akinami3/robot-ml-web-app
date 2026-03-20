"""
Audit log domain entity.
監査ログ ドメインエンティティ

このファイルでは、システムで行われた全ての操作を記録する「監査ログ」を
表現するデータ構造を定義しています。

監査ログとは:
- 誰が（user_id）、いつ（timestamp）、何をしたか（action）を記録するもの
- セキュリティ上重要で、不正アクセスの調査や操作の追跡に使われます
- 一般的なWebアプリケーションでは必須の機能です

例: 「ユーザーAが2024/01/15 10:30に緊急停止ボタンを押した」
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


# --- 監査対象のアクション（操作）を表す列挙型 ---
class AuditAction(str, enum.Enum):
    """
    記録対象となる操作の種類を表す列挙型。
    全ての重要な操作について、種類ごとに定義しています。

    カテゴリ別に整理:
    - 認証系: ログイン、ログアウト、トークン更新
    - ロボット操作系: 接続、切断、速度コマンド、ナビゲーション
    - 安全系: 緊急停止、操作ロック
    - データ系: 記録、データセット、エクスポート
    - RAG系: ドキュメント操作、AI質問
    - 管理系: ユーザー管理、設定変更
    """
    # --- 認証（Authentication）関連 ---
    LOGIN = "login"                     # ログイン
    LOGOUT = "logout"                   # ログアウト
    TOKEN_REFRESH = "token_refresh"     # JWTトークンの更新

    # --- ロボット操作（Robot Control）関連 ---
    ROBOT_CONNECT = "robot_connect"         # ロボットへの接続
    ROBOT_DISCONNECT = "robot_disconnect"   # ロボットからの切断
    VELOCITY_COMMAND = "velocity_command"   # 速度コマンドの送信（前進・旋回など）
    NAVIGATION_START = "navigation_start"   # 自律ナビゲーション開始
    NAVIGATION_CANCEL = "navigation_cancel" # 自律ナビゲーションのキャンセル

    # --- 安全（Safety）関連 ---
    ESTOP_ACTIVATE = "estop_activate"               # 緊急停止の発動
    ESTOP_RELEASE = "estop_release"                 # 緊急停止の解除
    OPERATION_LOCK_ACQUIRE = "operation_lock_acquire" # 操作ロックの取得（排他制御）
    OPERATION_LOCK_RELEASE = "operation_lock_release" # 操作ロックの解放

    # --- データ管理（Data Management）関連 ---
    RECORDING_START = "recording_start"   # センサーデータ記録の開始
    RECORDING_STOP = "recording_stop"     # センサーデータ記録の停止
    DATASET_CREATE = "dataset_create"     # データセットの作成
    DATASET_EXPORT = "dataset_export"     # データセットのエクスポート（ファイル出力）
    DATASET_DELETE = "dataset_delete"     # データセットの削除

    # --- RAG（AI質問応答）関連 ---
    DOCUMENT_UPLOAD = "document_upload"   # ドキュメントのアップロード
    DOCUMENT_DELETE = "document_delete"   # ドキュメントの削除
    RAG_QUERY = "rag_query"               # RAG質問の実行

    # --- 管理者（Admin）操作関連 ---
    USER_CREATE = "user_create"       # ユーザーの新規作成
    USER_UPDATE = "user_update"       # ユーザー情報の更新
    USER_DELETE = "user_delete"       # ユーザーの削除
    SETTINGS_CHANGE = "settings_change"   # システム設定の変更


# --- 監査ログエンティティ ---
@dataclass
class AuditLog:
    """
    1件の監査ログを表すデータクラス。

    システムで行われた1つの操作の記録です。
    「誰が、いつ、何を、どのリソースに対して行ったか」を記録します。

    Attributes:
        user_id: 操作を行ったユーザーのID
        action: 操作の種類（AuditAction列挙型）
        id: ログの一意なID
        resource_type: 操作対象の種類（例: "robot", "dataset"）
        resource_id: 操作対象のID（例: ロボットのUUID文字列）
        details: 操作の詳細情報（自由形式の辞書）
        ip_address: 操作元のIPアドレス（不正アクセス調査用）
        user_agent: ブラウザ情報（どの環境からアクセスしたか）
        timestamp: 操作日時
    """
    # --- 必須フィールド ---
    user_id: UUID           # 操作を行ったユーザーのID
    action: AuditAction     # 何をしたか（操作の種類）

    # --- オプションフィールド ---
    id: UUID = field(default_factory=uuid4)
    resource_type: str = ""     # 操作対象の種類（例: "robot", "dataset", "user"）
    resource_id: str = ""       # 操作対象の識別子
    details: dict[str, Any] = field(default_factory=dict)   # 詳細情報
    ip_address: str = ""        # アクセス元IPアドレス
    user_agent: str = ""        # ブラウザ/クライアント情報
    timestamp: datetime = field(default_factory=datetime.utcnow)   # 操作日時
