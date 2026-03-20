# =============================================================================
# Step 6: ロボット CRUD エンドポイント（インメモリ版）
# =============================================================================
#
# 【CRUD とは？】
# データ操作の基本4操作:
#   Create（作成）→ POST
#   Read（読取）  → GET
#   Update（更新）→ PUT / PATCH
#   Delete（削除）→ DELETE
#
# 【REST API の設計原則】
# リソース指向: URL はリソース（名詞）を表す → /robots
# HTTP メソッドで操作を表す:
#   GET    /robots      → 一覧取得
#   POST   /robots      → 新規作成
#   GET    /robots/{id} → 1件取得
#   PATCH  /robots/{id} → 部分更新
#   DELETE /robots/{id} → 削除
#
# 【なぜ POST /createRobot ではなく POST /robots ?】
# URL に動詞を入れると、操作が増えるたびに URL パスが増える。
# リソース + HTTP メソッドの組み合わせの方が、
# API が統一的かつ予測しやすいため、REST 設計ではこちらが推奨。
#
# 【インメモリ版の注意点】
# Step 6 ではデータベースを使わず、Python の辞書（dict）にデータを保存する。
# サーバーを再起動するとデータは消える。
# Step 7 でデータベース（PostgreSQL）を導入して永続化する。
#
# =============================================================================

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas import (
    MessageResponse,
    RobotCreate,
    RobotListResponse,
    RobotResponse,
    RobotStatus,
    RobotUpdate,
)

# =============================================================================
# APIRouter の作成
# =============================================================================
#
# 【APIRouter とは？】
# エンドポイントをグループ化するオブジェクト。
# main.py で `app.include_router(router, prefix="/api/v1")` とすると、
# このファイルの全エンドポイントが /api/v1 以下に登録される。
#
# Go の比較:
#   Go (gorilla/mux): r.HandleFunc("/robots", ListRobots).Methods("GET")
#   FastAPI:          @router.get("/robots")
#
router = APIRouter()

# =============================================================================
# インメモリ ストア
# =============================================================================
#
# 【辞書（dict）をデータストアとして使う】
# キーは UUID（一意な識別子）、値はロボットのデータ。
# Python の辞書検索は O(1)（ハッシュテーブル）なので、高速。
#
# Go との比較:
#   Go:     var robots = make(map[uuid.UUID]*Robot)
#   Python: robots: dict[UUID, dict] = {}
#
# 本番では辞書の代わりにデータベース（PostgreSQL）を使う → Step 7
#
robots_db: dict[UUID, dict] = {}

# --- サンプルデータの初期投入 ---
_sample_robots = [
    {
        "name": "TurtleBot3",
        "robot_type": "differential",
        "description": "教育・研究用差動二輪ロボット。ROS2 対応。",
    },
    {
        "name": "Scout Mini",
        "robot_type": "differential",
        "description": "屋外対応の小型自律移動ロボット。",
    },
    {
        "name": "MecanumBot",
        "robot_type": "omni",
        "description": "メカナムホイール搭載の全方向ロボット。",
    },
]

for sample in _sample_robots:
    _id = uuid4()
    _now = datetime.now(timezone.utc)
    robots_db[_id] = {
        "id": _id,
        "name": sample["name"],
        "robot_type": sample["robot_type"],
        "description": sample["description"],
        "status": RobotStatus.OFFLINE,
        "created_at": _now,
        "updated_at": _now,
    }


# =============================================================================
# GET /robots — ロボット一覧を取得
# =============================================================================
#
# 【response_model とは？】
# FastAPI が自動で行うレスポンスの「型チェック + JSON 変換」の定義。
# RobotListResponse に合わないデータがあればエラーになる。
# また、/docs の API ドキュメントにレスポンスの型が表示される。
#
# 【async def とは？】
# Python の非同期関数宣言。FastAPI は非同期（asyncio）で動作する。
# `await` を使って I/O 操作を非同期に実行できる。
# Step 6 では in-memory なので async の恩恵は薄いが、
# Step 7 で DB アクセスが入ると `await session.execute(...)` で活きてくる。
#
@router.get(
    "/robots",
    response_model=RobotListResponse,
    summary="ロボット一覧の取得",
    description="登録されているすべてのロボットの一覧を返す。",
)
async def list_robots():
    """全ロボットの一覧を取得する"""
    items = [RobotResponse(**data) for data in robots_db.values()]
    return RobotListResponse(robots=items, total=len(items))


# =============================================================================
# POST /robots — 新しいロボットを登録
# =============================================================================
#
# 【status_code=201 とは？】
# HTTP ステータスコード 201 Created: リソースが正常に作成された。
# デフォルトは 200 OK だが、Create 操作では 201 が適切。
#
# 【リクエストボディの自動バリデーション】
# `body: RobotCreate` と書くだけで、FastAPI が:
# 1. リクエストボディの JSON を読み取り
# 2. RobotCreate スキーマに変換を試み
# 3. バリデーションエラーがあれば 422 を自動で返す
# → 手動で JSON.parse したり、フィールドを1つずつチェックする必要がない！
#
@router.post(
    "/robots",
    response_model=RobotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ロボットの新規登録",
)
async def create_robot(body: RobotCreate):
    """
    新しいロボットを登録する。

    - **name**: ロボットの名前（必須、1-100文字）
    - **robot_type**: 駆動タイプ（differential / ackermann / omni）
    - **description**: 説明文（任意）
    """
    robot_id = uuid4()
    now = datetime.now(timezone.utc)

    robot_data = {
        "id": robot_id,
        "name": body.name,
        "robot_type": body.robot_type,
        "description": body.description,
        "status": RobotStatus.OFFLINE,
        "created_at": now,
        "updated_at": now,
    }

    robots_db[robot_id] = robot_data
    return RobotResponse(**robot_data)


# =============================================================================
# GET /robots/{robot_id} — 特定のロボットを取得
# =============================================================================
#
# 【パスパラメータ】
# {robot_id} は URL の一部で、実際の値に置き換わる。
# 例: GET /api/v1/robots/123e4567-e89b-12d3-a456-426614174000
#
# FastAPI は `robot_id: UUID` の型ヒントから、自動で:
# 1. パス文字列を UUID にパース
# 2. 不正な UUID なら 422 エラーを返す
#
# 【HTTPException とは？】
# HTTP エラーレスポンスを生成する例外。
# raise で投げると FastAPI がキャッチしてエラーレスポンスを返す。
# detail にはクライアントに返すエラーメッセージを書く。
#
@router.get(
    "/robots/{robot_id}",
    response_model=RobotResponse,
    summary="ロボットの詳細取得",
)
async def get_robot(robot_id: UUID):
    """指定された ID のロボットを取得する"""
    if robot_id not in robots_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ロボットが見つかりません: {robot_id}",
        )
    return RobotResponse(**robots_db[robot_id])


# =============================================================================
# PATCH /robots/{robot_id} — ロボット情報を部分更新
# =============================================================================
#
# 【PATCH と PUT の違い】
# PUT:   リソース全体を置き換える（全フィールド必須）
# PATCH: 送られたフィールドだけ更新する（部分更新）
#
# 多くの REST API では PATCH が便利なため好まれる。
# 「名前だけ変えたい」ときに全フィールドを送るのは面倒だから。
#
# 【exclude_unset=True の意味】
# `body.model_dump(exclude_unset=True)` で、
# クライアントが「明示的に送った」フィールドだけ辞書に含める。
# None が「送られていない」のか「意図的に None」なのかを区別できる。
#
@router.patch(
    "/robots/{robot_id}",
    response_model=RobotResponse,
    summary="ロボット情報の部分更新",
)
async def update_robot(robot_id: UUID, body: RobotUpdate):
    """指定された ID のロボット情報を更新する（部分更新）"""
    if robot_id not in robots_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ロボットが見つかりません: {robot_id}",
        )

    # --- 部分更新ロジック ---
    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新するフィールドが指定されていません",
        )

    robot = robots_db[robot_id]
    for field, value in update_data.items():
        robot[field] = value

    robot["updated_at"] = datetime.now(timezone.utc)

    return RobotResponse(**robot)


# =============================================================================
# DELETE /robots/{robot_id} — ロボットを削除
# =============================================================================
#
# 【204 No Content vs 200 OK】
# 削除成功時に 204 を返すのが REST の一般的パターン。
# 204 はレスポンスボディが「空」であることを意味する。
# ただし、削除されたリソースの情報を返したい場合は 200 でもよい。
# ここでは確認メッセージを返すため 200 を使用。
#
@router.delete(
    "/robots/{robot_id}",
    response_model=MessageResponse,
    summary="ロボットの削除",
)
async def delete_robot(robot_id: UUID):
    """指定された ID のロボットを削除する"""
    if robot_id not in robots_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ロボットが見つかりません: {robot_id}",
        )

    robot = robots_db.pop(robot_id)
    return MessageResponse(message=f"ロボット '{robot['name']}' を削除しました")
