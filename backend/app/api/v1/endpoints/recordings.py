"""Recording session endpoints."""

# =============================================================================
# 記録セッション（Recording Session）エンドポイント
# =============================================================================
# このファイルでは、ロボットのセンサーデータを記録するための
# セッション管理APIを定義しています。
#
# 主な機能:
#   - 記録の開始（POST /recordings）
#   - 記録の停止（POST /recordings/{session_id}/stop）
#   - 記録一覧の取得（GET /recordings）
#   - 記録詳細の取得（GET /recordings/{session_id}）
#
# 「セッション」とは？
#   記録の開始から停止までの一連の流れを「記録セッション」と呼びます。
#   1つのセッションには、どのセンサーを使うか、最大周波数はいくつか、
#   などの設定（RecordingConfig）が紐づいています。
# =============================================================================

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

# --- ドメイン層からのインポート ---
# AuditAction: 監査ログに記録する操作の種類（開始・停止など）
from ....domain.entities.audit_log import AuditAction

# RecordingConfig: 記録セッションの設定（どのセンサーを使うか等）
from ....domain.entities.recording import RecordingConfig

# SensorType: センサーの種類（カメラ、LiDAR、IMUなど）を表す列挙型
from ....domain.entities.sensor_data import SensorType

# --- 依存性注入（Dependency Injection）---
# AuditSvc: 監査ログサービス（操作履歴を記録する）
# CurrentUser: 現在ログイン中のユーザー（閲覧権限あり）
# OperatorUser: オペレーター以上の権限を持つユーザー（操作権限あり）
# RecordingSvc: 記録セッションの管理サービス
from ..dependencies import AuditSvc, CurrentUser, OperatorUser, RecordingSvc

# --- リクエスト/レスポンスのスキーマ ---
from ..schemas import RecordingResponse, RecordingStartRequest

# ルーターの作成: /recordings 以下のエンドポイントをまとめる
router = APIRouter(prefix="/recordings", tags=["recordings"])


# =============================================================================
# 記録開始エンドポイント（POST /recordings）
# =============================================================================
# 新しい記録セッションを開始します。
# OperatorUser のみ実行可能（管理者またはオペレーター権限が必要）
# 一般ユーザー（viewer）はこの操作を実行できません。
# =============================================================================
@router.post("", response_model=RecordingResponse, status_code=201)
async def start_recording(
    body: RecordingStartRequest,
    # OperatorUser: オペレーター以上の権限チェック
    # 権限が足りない場合は自動的に403エラーが返される
    current_user: OperatorUser,
    recording_svc: RecordingSvc,
    audit_svc: AuditSvc,
):
    # -----------------------------------------------------------------
    # ステップ1: センサータイプのバリデーション（検証）
    # -----------------------------------------------------------------
    # リクエストで指定されたセンサータイプ文字列を、
    # SensorType列挙型に変換します。
    # forループで1つずつチェックし、無効な値があれば400エラーを返します。
    # 例: "camera" → SensorType.CAMERA（有効）
    #      "invalid" → ValueError（無効 → 400エラー）
    sensor_types = []
    for st_str in body.sensor_types:
        try:
            sensor_types.append(SensorType(st_str))
        except ValueError:
            # 無効なセンサータイプが含まれていた場合、400 Bad Requestを返す
            raise HTTPException(
                status_code=400, detail=f"Invalid sensor type: {st_str}"
            )

    # -----------------------------------------------------------------
    # ステップ2: 最大周波数の変換
    # -----------------------------------------------------------------
    # センサーごとの最大記録周波数（Hz）を辞書形式で変換します。
    # 無効なセンサータイプのキーは無視します（passで飛ばす）
    max_freq = {}
    for st_str, freq in body.max_frequency_hz.items():
        try:
            max_freq[SensorType(st_str)] = freq
        except ValueError:
            # 不明なセンサータイプは無視して次へ進む
            pass

    # -----------------------------------------------------------------
    # ステップ3: RecordingConfig（記録設定）の作成
    # -----------------------------------------------------------------
    # バリデーション済みのセンサータイプと最大周波数から
    # 記録設定オブジェクトを生成します。
    config = RecordingConfig(
        sensor_types=sensor_types,
        max_frequency_hz=max_freq,
    )

    # -----------------------------------------------------------------
    # ステップ4: 記録セッションの開始
    # -----------------------------------------------------------------
    # RecordingSvcを使って新しい記録セッションを開始します。
    # すでに同じロボットで記録中の場合はValueError → 409 Conflictを返す
    try:
        session = await recording_svc.start_recording(
            robot_id=body.robot_id,
            user_id=current_user.id,
            config=config,
        )
    except ValueError as e:
        # 競合エラー（例: 同じロボットがすでに記録中）
        raise HTTPException(status_code=409, detail=str(e))

    # -----------------------------------------------------------------
    # ステップ5: 監査ログに記録開始を記録
    # -----------------------------------------------------------------
    # 誰が、いつ、どのロボットの記録を開始したかを監査ログに保存します。
    # セキュリティや運用管理のために重要な記録です。
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.RECORDING_START,
        resource_type="recording",
        resource_id=str(session.id),
        details={
            "robot_id": str(body.robot_id),
            "sensor_types": body.sensor_types,
        },
    )

    # ステップ6: レスポンスを返す
    return RecordingResponse(
        id=session.id,
        robot_id=session.robot_id,
        user_id=session.user_id,
        is_active=session.is_active,
        record_count=session.record_count,
        size_bytes=session.size_bytes,
        started_at=session.started_at,
        stopped_at=session.stopped_at,
        config={
            "sensor_types": [st.value for st in session.config.sensor_types],
            "enabled": session.config.enabled,
        },
    )


# =============================================================================
# 記録停止エンドポイント（POST /recordings/{session_id}/stop）
# =============================================================================
# 指定されたセッションIDの記録を停止します。
# 開始と同様、OperatorUser（管理者/オペレーター）のみ実行可能です。
#
# 【開始 vs 停止の流れ】
#   開始: センサー検証 → 設定作成 → セッション開始 → 監査ログ
#   停止: セッション停止 → 存在チェック → 監査ログ
#   停止の方がシンプルで、設定の検証は不要です。
# =============================================================================
@router.post("/{session_id}/stop", response_model=RecordingResponse)
async def stop_recording(
    session_id: UUID,
    # オペレーター以上の権限が必要（管理者/オペレーターのみ操作可能）
    current_user: OperatorUser,
    recording_svc: RecordingSvc,
    audit_svc: AuditSvc,
):
    # セッションを停止する（is_active が False になる）
    session = await recording_svc.stop_recording(session_id)

    # セッションが見つからない場合は404エラー
    if session is None:
        raise HTTPException(status_code=404, detail="Recording session not found")

    # 監査ログに記録停止を記録
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.RECORDING_STOP,
        resource_type="recording",
        resource_id=str(session_id),
        details={"record_count": session.record_count},
    )

    return RecordingResponse(
        id=session.id,
        robot_id=session.robot_id,
        user_id=session.user_id,
        is_active=session.is_active,
        record_count=session.record_count,
        size_bytes=session.size_bytes,
        started_at=session.started_at,
        stopped_at=session.stopped_at,
        config={
            "sensor_types": [st.value for st in session.config.sensor_types],
            "enabled": session.config.enabled,
        },
    )


# =============================================================================
# 記録一覧取得エンドポイント（GET /recordings）
# =============================================================================
# ログイン中のユーザーが所有する記録セッションの一覧を返します。
# CurrentUser（一般ユーザーを含む全ユーザー）がアクセス可能です。
# ※ 閲覧のみなので、OperatorUserではなくCurrentUserで十分です。
# =============================================================================
@router.get("", response_model=list[RecordingResponse])
async def list_recordings(
    # CurrentUser: ログイン済みであれば誰でもOK（閲覧権限）
    current_user: CurrentUser,
    recording_svc: RecordingSvc,
):
    # 現在のユーザーに紐づく全セッションを取得
    sessions = await recording_svc.get_user_sessions(current_user.id)

    # リスト内包表記で各セッションをレスポンス形式に変換
    return [
        RecordingResponse(
            id=s.id,
            robot_id=s.robot_id,
            user_id=s.user_id,
            is_active=s.is_active,
            record_count=s.record_count,
            size_bytes=s.size_bytes,
            started_at=s.started_at,
            stopped_at=s.stopped_at,
            config={
                "sensor_types": [st.value for st in s.config.sensor_types],
                "enabled": s.config.enabled,
            },
        )
        for s in sessions
    ]


# =============================================================================
# 記録詳細取得エンドポイント（GET /recordings/{session_id}）
# =============================================================================
# 指定されたセッションIDの詳細情報を返します。
# CurrentUser（一般ユーザーを含む全ユーザー）がアクセス可能です。
# =============================================================================
@router.get("/{session_id}", response_model=RecordingResponse)
async def get_recording(
    # パスパラメータ: URLに含まれるセッションID（UUID形式）
    session_id: UUID,
    current_user: CurrentUser,
    recording_svc: RecordingSvc,
):
    # セッションIDで記録セッションを検索
    session = await recording_svc.get_session(session_id)

    # 見つからなければ404エラーを返す
    if session is None:
        raise HTTPException(status_code=404, detail="Recording session not found")

    return RecordingResponse(
        id=session.id,
        robot_id=session.robot_id,
        user_id=session.user_id,
        is_active=session.is_active,
        record_count=session.record_count,
        size_bytes=session.size_bytes,
        started_at=session.started_at,
        stopped_at=session.stopped_at,
        config={
            "sensor_types": [st.value for st in session.config.sensor_types],
            "enabled": session.config.enabled,
        },
    )
