"""Robot management endpoints."""

# =============================================================================
# ロボット管理 API エンドポイント
# =============================================================================
#
# このファイルでは、ロボットの CRUD（作成・読み取り・更新・削除）操作を
# REST API として提供します。
#
# REST API の基本パターン:
#   GET    /robots          → 一覧取得（リスト）
#   GET    /robots/{id}     → 個別取得（1件）
#   POST   /robots          → 新規作成
#   PATCH  /robots/{id}     → 部分更新
#   DELETE /robots/{id}     → 削除
#
# HTTP メソッドと操作の対応:
#   GET    = データの取得（安全・副作用なし）
#   POST   = 新しいリソースの作成
#   PATCH  = 既存リソースの部分的な更新
#   DELETE = リソースの削除
# =============================================================================

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ....domain.entities.audit_log import AuditAction
from ....domain.entities.robot import Robot
from ..dependencies import AuditSvc, CurrentUser, OperatorUser, RobotRepo
from ..schemas import RobotCreate, RobotResponse, RobotUpdate

# -----------------------------------------------------------------------------
# ルーターの設定
# -----------------------------------------------------------------------------
# prefix="/robots" → すべてのエンドポイントに /robots が付きます
# tags=["robots"]  → Swagger UI（APIドキュメント）でグループ分けされます
router = APIRouter(prefix="/robots", tags=["robots"])


# =============================================================================
# GET /robots — ロボット一覧取得
# =============================================================================
# ログインしているユーザーなら誰でもアクセスできます（CurrentUser）
#
# クエリパラメータ（query parameters）:
#   offset: 何件目から取得するか（デフォルト: 0 = 最初から）
#   limit:  最大何件取得するか（デフォルト: 100件）
#   → URL例: GET /robots?offset=0&limit=20
#
# クエリパラメータ vs パスパラメータの違い:
#   クエリパラメータ → ?key=value の形式。フィルタや検索条件に使う
#   パスパラメータ   → /robots/{robot_id} の形式。特定リソースの指定に使う
# =============================================================================
@router.get("", response_model=list[RobotResponse])
async def list_robots(
    current_user: CurrentUser,
    robot_repo: RobotRepo,
    offset: int = 0,
    limit: int = 100,
):
    # リポジトリからロボット一覧を取得（ページネーション対応）
    robots = await robot_repo.get_all(offset=offset, limit=limit)

    # -----------------------------------------------------------------------
    # リスト内包表記（list comprehension）でドメインオブジェクトをレスポンスに変換
    # -----------------------------------------------------------------------
    # ドメインエンティティ（Robot）には内部的なデータ構造があります。
    # それを API レスポンス用の形式（RobotResponse）に変換しています。
    #
    # 内包表記の書き方:
    #   [変換処理(item) for item in リスト]
    #
    # 通常の for ループで書くと:
    #   result = []
    #   for r in robots:
    #       result.append(RobotResponse(...))
    #   return result
    #
    # r.state.value → Enum（列挙型）の値を文字列に変換
    # c.value for c in r.capabilities → 各機能（Enum）を文字列リストに変換
    # -----------------------------------------------------------------------
    return [
        RobotResponse(
            id=r.id,
            name=r.name,
            adapter_type=r.adapter_type,
            state=r.state.value,
            capabilities=[c.value for c in r.capabilities],
            battery_level=r.battery_level,
            last_seen=r.last_seen,
            created_at=r.created_at,
        )
        for r in robots
    ]


# =============================================================================
# GET /robots/{robot_id} — 特定のロボットを取得
# =============================================================================
# パスパラメータ（path parameter）:
#   robot_id: URL の一部としてロボットの UUID を指定します
#   → URL例: GET /robots/550e8400-e29b-41d4-a716-446655440000
#
# FastAPI はパスパラメータを自動的に UUID 型に変換・バリデーションします。
# 不正な形式の場合は 422 Validation Error が返されます。
# =============================================================================
@router.get("/{robot_id}", response_model=RobotResponse)
async def get_robot(
    robot_id: UUID,
    current_user: CurrentUser,
    robot_repo: RobotRepo,
):
    robot = await robot_repo.get_by_id(robot_id)
    # ロボットが見つからなければ 404 Not Found を返す
    if robot is None:
        raise HTTPException(status_code=404, detail="Robot not found")
    return RobotResponse(
        id=robot.id,
        name=robot.name,
        adapter_type=robot.adapter_type,
        state=robot.state.value,
        capabilities=[c.value for c in robot.capabilities],
        battery_level=robot.battery_level,
        last_seen=robot.last_seen,
        created_at=robot.created_at,
    )


# =============================================================================
# POST /robots — 新しいロボットを作成
# =============================================================================
# 認可（authorization）の違い:
#   CurrentUser  → ログインしていれば誰でもOK（閲覧系に使用）
#   OperatorUser → オペレーター権限が必要（変更系に使用）
#
# このエンドポイントは OperatorUser を使用しているため、
# オペレーター以上の権限を持つユーザーのみがロボットを作成できます。
# 権限がないユーザーがアクセスすると 403 Forbidden が返されます。
#
# status_code=201 → リソースの作成成功を示す HTTP ステータスコード
# （通常の成功は 200 ですが、新規作成は 201 Created が標準です）
# =============================================================================
@router.post("", response_model=RobotResponse, status_code=201)
async def create_robot(
    body: RobotCreate,
    current_user: OperatorUser,
    robot_repo: RobotRepo,
    audit_svc: AuditSvc,
):
    # 同じ名前のロボットが既に存在するかチェック（重複防止）
    existing = await robot_repo.get_by_name(body.name)
    if existing is not None:
        # 409 Conflict → リソースが既に存在する場合のエラーコード
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Robot name already exists",
        )

    # ドメインエンティティを作成してリポジトリに保存
    robot = Robot(
        name=body.name,
        adapter_type=body.adapter_type,
        connection_params=body.connection_params,
    )
    created = await robot_repo.create(robot)

    # -----------------------------------------------------------------------
    # 監査ログ（Audit Log）の記録
    # -----------------------------------------------------------------------
    # 重要な操作（作成・削除など）は監査ログに記録します。
    # これにより「誰が・いつ・何をしたか」を追跡できます。
    # セキュリティやコンプライアンスの観点で非常に重要です。
    #
    # 記録する情報:
    #   user_id       → 操作したユーザー
    #   action        → 実行したアクション（ロボット接続）
    #   resource_type → 対象リソースの種類
    #   resource_id   → 対象リソースの ID
    # -----------------------------------------------------------------------
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.ROBOT_CONNECT,
        resource_type="robot",
        resource_id=str(created.id),
    )

    return RobotResponse(
        id=created.id,
        name=created.name,
        adapter_type=created.adapter_type,
        state=created.state.value,
        capabilities=[c.value for c in created.capabilities],
        battery_level=created.battery_level,
        last_seen=created.last_seen,
        created_at=created.created_at,
    )


# =============================================================================
# PATCH /robots/{robot_id} — ロボット情報の部分更新
# =============================================================================
# PATCH vs PUT の違い:
#   PATCH → 一部のフィールドだけを更新（部分更新）
#   PUT   → リソース全体を置き換え（全体更新）
#
# ここでは PATCH を使っているので、変更したいフィールドだけを
# リクエストボディに含めればOKです。
# 例: {"name": "新しい名前"} → 名前だけ更新、他はそのまま
#
# OperatorUser が必要 → オペレーター権限でのみ更新可能
# =============================================================================
@router.patch("/{robot_id}", response_model=RobotResponse)
async def update_robot(
    robot_id: UUID,
    body: RobotUpdate,
    current_user: OperatorUser,
    robot_repo: RobotRepo,
):
    robot = await robot_repo.get_by_id(robot_id)
    if robot is None:
        raise HTTPException(status_code=404, detail="Robot not found")

    # body のフィールドが None でなければ（＝送信されていれば）更新する
    # この「None チェック」が PATCH の部分更新を実現するパターンです
    if body.name is not None:
        robot.name = body.name
    if body.connection_params is not None:
        robot.connection_params = body.connection_params

    updated = await robot_repo.update(robot)
    return RobotResponse(
        id=updated.id,
        name=updated.name,
        adapter_type=updated.adapter_type,
        state=updated.state.value,
        capabilities=[c.value for c in updated.capabilities],
        battery_level=updated.battery_level,
        last_seen=updated.last_seen,
        created_at=updated.created_at,
    )


# =============================================================================
# DELETE /robots/{robot_id} — ロボットを削除
# =============================================================================
# status_code=204 → No Content（削除成功、レスポンスボディなし）
# DELETE は成功時にデータを返さないのが REST の慣例です。
#
# OperatorUser が必要 → オペレーター権限でのみ削除可能
# 削除操作も監査ログに記録されます（セキュリティ上重要な操作のため）
# =============================================================================
@router.delete("/{robot_id}", status_code=204)
async def delete_robot(
    robot_id: UUID,
    current_user: OperatorUser,
    robot_repo: RobotRepo,
    audit_svc: AuditSvc,
):
    deleted = await robot_repo.delete(robot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Robot not found")

    # 削除時も監査ログを記録（誰がどのロボットを削除したか追跡可能にする）
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.ROBOT_DISCONNECT,
        resource_type="robot",
        resource_id=str(robot_id),
    )
