# ============================================================
# gRPC ゲートウェイクライアント（Gateway gRPC Client）
# ============================================================
# Go で書かれた Gateway サービスと gRPC で通信するクライアントです。
#
# 【gRPC とは？】
# Google が開発した高速通信プロトコル。
# REST API（JSON + HTTP）と比べて：
# - Protocol Buffers（バイナリ形式）で通信 → 高速・省メモリ
# - 双方向ストリーミング対応
# - 型安全（proto ファイルでスキーマを定義）
#
# 【注意: 現在はプレースホルダー】
# 完全な gRPC クライアントを使うには、proto ファイルから
# Python のスタブ（自動生成コード）を作る必要があります。
# scripts/generate-proto.sh でスタブを生成してください。
#
# 【ゲートウェイの役割】
# Gateway は Go で書かれたサービスで、以下を担当：
# - WebSocket でフロントエンドとリアルタイム通信
# - ロボットアダプターの管理
# - コマンドの中継（バックエンド → ロボット）
# - 緊急停止の処理
# ============================================================
"""gRPC client for Gateway communication.

NOTE: This is a placeholder. Full gRPC client requires generated protobuf code.
Run scripts/generate-proto.sh to generate the Python gRPC stubs, then update imports.
"""

from __future__ import annotations

import structlog
from typing import Any

logger = structlog.get_logger()


class GatewayGRPCClient:
    """
    Go Gateway サービスとの gRPC 通信クライアント。

    【現在の状態】
    proto ファイルからのスタブ生成が必要なため、
    各メソッドはプレースホルダー（仮実装）です。
    ログ出力と固定値の返却のみ行います。
    """

    def __init__(self, gateway_url: str = "gateway:50051") -> None:
        """
        コンストラクタ。

        Args:
            gateway_url: Gateway サービスのアドレス
                "gateway" は Docker Compose のサービス名
                50051 は gRPC のデフォルトポート
        """
        self._url = gateway_url
        self._channel = None  # gRPC チャンネル（接続を保持）

    async def connect(self) -> None:
        """
        gRPC チャンネル（接続）を確立する。

        【grpc.aio.insecure_channel とは？】
        暗号化なし（TLS なし）の gRPC チャンネルを作成。
        Docker 内部通信では暗号化不要のため insecure を使用。
        本番環境では secure_channel（TLS対応）を使うべき。
        """
        try:
            import grpc
            self._channel = grpc.aio.insecure_channel(self._url)
            logger.info("grpc_channel_connected", url=self._url)
        except ImportError:
            # grpc ライブラリがインストールされていない場合
            logger.warning("grpc not available, gateway communication disabled")

    async def close(self) -> None:
        """gRPC チャンネルを閉じる。"""
        if self._channel is not None:
            await self._channel.close()

    async def send_command(
        self, robot_id: str, command_type: str, payload: dict
    ) -> dict:
        """
        Gateway 経由でロボットにコマンドを送信する。

        【コマンドの例】
        - move: 移動指示（速度、角速度）
        - arm: アーム操作（関節角度）
        - gripper: グリッパー操作（開閉）

        Args:
            robot_id: コマンド送信先のロボットID
            command_type: コマンドの種類（"move", "arm" 等）
            payload: コマンドのパラメータ（辞書形式）
        Returns:
            送信結果の辞書
        """
        # TODO: 生成された protobuf スタブを使って実装
        logger.info(
            "grpc_send_command",
            robot_id=robot_id,
            command_type=command_type,
        )
        return {"status": "ok", "message": "Command sent"}

    async def emergency_stop(self, robot_id: str, reason: str = "") -> bool:
        """
        特定のロボットを緊急停止する。

        【緊急停止（E-Stop）とは？】
        安全上の理由で、ロボットの全動作を即座に停止する機能。
        最優先で処理され、他のコマンドよりも高い優先度を持つ。

        Args:
            robot_id: 停止するロボットのID
            reason: 停止理由
        Returns:
            停止コマンドの送信に成功したら True
        """
        logger.warning(
            "grpc_emergency_stop",
            robot_id=robot_id,
            reason=reason,
        )
        return True

    async def emergency_stop_all(self, reason: str = "") -> bool:
        """
        全ロボットを緊急停止する。

        システム全体に影響する緊急事態の場合に使用。

        Args:
            reason: 停止理由
        Returns:
            停止コマンドの送信に成功したら True
        """
        logger.warning("grpc_emergency_stop_all", reason=reason)
        return True

    async def get_robot_status(self, robot_id: str) -> dict:
        """
        Gateway からロボットの現在状態を取得する。

        Args:
            robot_id: 状態を確認するロボットのID
        Returns:
            ロボットの状態情報（辞書形式）
        """
        return {
            "robot_id": robot_id,
            "state": "unknown",
            "message": "gRPC not fully implemented",
        }

    async def list_connected_robots(self) -> list[dict]:
        """
        Gateway に接続中の全ロボット一覧を取得する。

        Returns:
            接続中のロボット情報のリスト
        """
        return []

    async def health_check(self) -> bool:
        """
        Gateway の gRPC サービスの稼働確認。

        gRPC チャンネルの接続状態を確認して、
        READY（接続準備完了）なら True を返す。

        Returns:
            サービスが正常に接続されていれば True
        """
        if self._channel is None:
            return False
        try:
            import grpc
            state = self._channel.get_state()
            return state == grpc.ChannelConnectivity.READY
        except Exception:
            return False
