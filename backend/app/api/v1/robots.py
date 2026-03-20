# =============================================================================
# Step 8: ロボット CRUD エンドポイント（認証保護版）
# =============================================================================
#
# 【Step 7 からの変更点】
# Step 7: 誰でもアクセス可能（認証なし）
# Step 8: JWT 認証 + ロールベースアクセス制御を追加
#
# 【エンドポイントごとの権限設計】
#   GET    /robots       → 認証済みユーザー全員（viewer 以上）
#   POST   /robots       → operator 以上
#   GET    /robots/{id}  → 認証済みユーザー全員
#   PATCH  /robots/{id}  → operator 以上
#   DELETE /robots/{id}  → admin のみ
#
# 権限のグラデーション:
#   viewer < operator < admin
#
# =============================================================================

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas import (
    MessageResponse,
    RobotCreate,
    RobotListResponse,
    RobotResponse,
    RobotUpdate,
)
from app.api.v1.dependencies import (
    get_robot_repository,
    get_current_user,
    require_role,
)
from app.domain.entities.robot import Robot, RobotStatus, RobotType
from app.domain.entities.user import User
from app.domain.repositories.robot_repo import RobotRepository

router = APIRouter()


def _to_response(entity: Robot) -> RobotResponse:
    """ドメインエンティティ → レスポンススキーマ"""
    return RobotResponse(
        id=entity.id,
        name=entity.name,
        robot_type=entity.robot_type.value,
        description=entity.description,
        status=entity.status.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


# =============================================================================
# GET /robots — ロボット一覧（認証済み全ユーザー）
# =============================================================================
#
# 【Depends(get_current_user) を追加するだけで認証保護】
# Step 7 の `async def list_robots(repo=...)` に
# `current_user: User = Depends(get_current_user)` を追加するだけ。
#
# JWT なし → 401 Unauthorized
# JWT あり → ユーザー情報が current_user に入る
#
@router.get(
    "/robots",
    response_model=RobotListResponse,
    summary="ロボット一覧の取得",
)
async def list_robots(
    current_user: User = Depends(get_current_user),
    repo: RobotRepository = Depends(get_robot_repository),
):
    """全ロボットの一覧を取得する（要認証）"""
    robots = await repo.list_all()
    items = [_to_response(r) for r in robots]
    total = await repo.count()
    return RobotListResponse(robots=items, total=total)


# =============================================================================
# POST /robots — 新規登録（operator 以上）
# =============================================================================
#
# 【require_role() の使い方】
# Depends(require_role("admin", "operator"))
# → admin か operator のみ許可。viewer は 403 Forbidden。
#
@router.post(
    "/robots",
    response_model=RobotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ロボットの新規登録",
)
async def create_robot(
    body: RobotCreate,
    current_user: User = Depends(require_role("admin", "operator")),
    repo: RobotRepository = Depends(get_robot_repository),
):
    """新しいロボットを登録する（operator 以上）"""
    entity = Robot(
        name=body.name,
        robot_type=RobotType(body.robot_type),
        description=body.description,
    )
    created = await repo.create(entity)
    return _to_response(created)


# =============================================================================
# GET /robots/{robot_id} — 詳細取得（認証済み全ユーザー）
# =============================================================================
@router.get(
    "/robots/{robot_id}",
    response_model=RobotResponse,
    summary="ロボットの詳細取得",
)
async def get_robot(
    robot_id: UUID,
    current_user: User = Depends(get_current_user),
    repo: RobotRepository = Depends(get_robot_repository),
):
    """指定された ID のロボットを取得する（要認証）"""
    robot = await repo.get_by_id(robot_id)
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ロボットが見つかりません: {robot_id}",
        )
    return _to_response(robot)


# =============================================================================
# PATCH /robots/{robot_id} — 部分更新（operator 以上）
# =============================================================================
@router.patch(
    "/robots/{robot_id}",
    response_model=RobotResponse,
    summary="ロボット情報の部分更新",
)
async def update_robot(
    robot_id: UUID,
    body: RobotUpdate,
    current_user: User = Depends(require_role("admin", "operator")),
    repo: RobotRepository = Depends(get_robot_repository),
):
    """指定された ID のロボット情報を更新する（operator 以上）"""
    robot = await repo.get_by_id(robot_id)
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ロボットが見つかりません: {robot_id}",
        )

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新するフィールドが指定されていません",
        )

    if "name" in update_data:
        robot.name = update_data["name"]
    if "robot_type" in update_data:
        robot.robot_type = RobotType(update_data["robot_type"])
    if "description" in update_data:
        robot.description = update_data["description"]
    if "status" in update_data:
        robot.status = RobotStatus(update_data["status"])

    updated = await repo.update(robot)
    return _to_response(updated)


# =============================================================================
# DELETE /robots/{robot_id} — 削除（admin のみ）
# =============================================================================
#
# 【admin のみに制限する理由】
# 削除は取り消しが難しい操作。最小権限の原則に従い、
# admin だけが実行できるようにする。
#
@router.delete(
    "/robots/{robot_id}",
    response_model=MessageResponse,
    summary="ロボットの削除",
)
async def delete_robot(
    robot_id: UUID,
    current_user: User = Depends(require_role("admin")),
    repo: RobotRepository = Depends(get_robot_repository),
):
    """指定された ID のロボットを削除する（admin のみ）"""
    robot = await repo.get_by_id(robot_id)
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ロボットが見つかりません: {robot_id}",
        )

    await repo.delete(robot_id)
    return MessageResponse(message=f"ロボット '{robot.name}' を削除しました")
