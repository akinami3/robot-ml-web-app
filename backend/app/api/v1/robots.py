# =============================================================================
# Step 7: ロボット CRUD エンドポイント（データベース版）
# =============================================================================
#
# 【Step 6 からの変更点】
# Step 6: インメモリ辞書 (robots_db: dict) にデータを保存
# Step 7: PostgreSQL データベースに永続化
#
# 【変わったこと】
# 1. `robots_db = {}` → `RobotRepository` (DI で注入)
# 2. `uuid4()` で ID 生成 → DB が UUID を自動生成
# 3. 辞書操作 → `await repo.create()`, `await repo.list_all()` など
# 4. データがサーバー再起動後も残る！
#
# 【変わらなかったこと】
# - URL パス（/robots, /robots/{id}）
# - HTTP メソッド（GET, POST, PATCH, DELETE）
# - リクエスト/レスポンスの形式（schemas.py は同じ）
# - ステータスコード（200, 201, 404 など）
# → REST API の設計が良ければ、内部実装の変更がインターフェースに影響しない！
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
from app.api.v1.dependencies import get_robot_repository
from app.domain.entities.robot import Robot, RobotStatus, RobotType
from app.domain.repositories.robot_repo import RobotRepository

# =============================================================================
# APIRouter の作成
# =============================================================================
router = APIRouter()


# =============================================================================
# ヘルパー: ドメインエンティティ → レスポンススキーマ 変換
# =============================================================================
#
# 【なぜ変換が必要？】
# Robot (dataclass) と RobotResponse (Pydantic) は別の型。
# ORM → Entity はリポジトリが担当。
# Entity → Response は API 層が担当。
#
# Pydantic v2 の model_validate() で変換する。
#
def _to_response(entity: Robot) -> RobotResponse:
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
# GET /robots — ロボット一覧を取得
# =============================================================================
#
# 【Depends() による DI】
# `repo: RobotRepository = Depends(get_robot_repository)`
#
# FastAPI がリクエスト処理時に自動で:
# 1. get_session() を呼んで DB セッションを取得
# 2. get_robot_repository(session) を呼んでリポジトリを生成
# 3. そのリポジトリを repo パラメータに注入
# 4. リクエスト完了後、セッションを自動で close
#
# エンドポイント関数は「リポジトリがある」ことだけ知っていればよく、
# DB 接続の詳細は一切知らなくてよい。
#
@router.get(
    "/robots",
    response_model=RobotListResponse,
    summary="ロボット一覧の取得",
    description="登録されているすべてのロボットの一覧を返す。",
)
async def list_robots(
    repo: RobotRepository = Depends(get_robot_repository),
):
    """全ロボットの一覧を取得する"""
    robots = await repo.list_all()
    items = [_to_response(r) for r in robots]
    total = await repo.count()
    return RobotListResponse(robots=items, total=total)


# =============================================================================
# POST /robots — 新しいロボットを登録
# =============================================================================
#
# 【ドメインエンティティの生成】
# API 層でリクエスト (RobotCreate) → ドメインエンティティ (Robot) に変換し、
# リポジトリに渡して永続化する。
#
# 変換の流れ:
#   RobotCreate (Pydantic) → Robot (dataclass) → RobotModel (ORM) → DB
#   ↑ API 層                  ↑ ドメイン層        ↑ インフラ層
#
@router.post(
    "/robots",
    response_model=RobotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ロボットの新規登録",
)
async def create_robot(
    body: RobotCreate,
    repo: RobotRepository = Depends(get_robot_repository),
):
    """新しいロボットを登録する"""
    # Pydantic スキーマ → ドメインエンティティ
    entity = Robot(
        name=body.name,
        robot_type=RobotType(body.robot_type),
        description=body.description,
    )

    created = await repo.create(entity)
    return _to_response(created)


# =============================================================================
# GET /robots/{robot_id} — 特定のロボットを取得
# =============================================================================
@router.get(
    "/robots/{robot_id}",
    response_model=RobotResponse,
    summary="ロボットの詳細取得",
)
async def get_robot(
    robot_id: UUID,
    repo: RobotRepository = Depends(get_robot_repository),
):
    """指定された ID のロボットを取得する"""
    robot = await repo.get_by_id(robot_id)
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ロボットが見つかりません: {robot_id}",
        )
    return _to_response(robot)


# =============================================================================
# PATCH /robots/{robot_id} — ロボット情報を部分更新
# =============================================================================
#
# 【部分更新のロジック変更】
# Step 6: dict を直接書き換え
# Step 7: エンティティを取得 → フィールド更新 → リポジトリで保存
#
# exclude_unset=True は同じ。
# 「送られたフィールドだけ」を更新する PATCH の仕様は変わらない。
#
@router.patch(
    "/robots/{robot_id}",
    response_model=RobotResponse,
    summary="ロボット情報の部分更新",
)
async def update_robot(
    robot_id: UUID,
    body: RobotUpdate,
    repo: RobotRepository = Depends(get_robot_repository),
):
    """指定された ID のロボット情報を更新する（部分更新）"""
    # --- 既存データの取得 ---
    robot = await repo.get_by_id(robot_id)
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ロボットが見つかりません: {robot_id}",
        )

    # --- 部分更新: 送られたフィールドだけ書き換え ---
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
# DELETE /robots/{robot_id} — ロボットを削除
# =============================================================================
@router.delete(
    "/robots/{robot_id}",
    response_model=MessageResponse,
    summary="ロボットの削除",
)
async def delete_robot(
    robot_id: UUID,
    repo: RobotRepository = Depends(get_robot_repository),
):
    """指定された ID のロボットを削除する"""
    # 削除前に名前を取得（メッセージ用）
    robot = await repo.get_by_id(robot_id)
    if robot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ロボットが見つかりません: {robot_id}",
        )

    await repo.delete(robot_id)
    return MessageResponse(message=f"ロボット '{robot.name}' を削除しました")
