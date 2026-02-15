"""Dataset management endpoints."""
# =============================================================================
# データセット管理エンドポイント
# =============================================================================
# このファイルでは、データセット（学習用データの集まり）に対する
# CRUD操作（作成・読み取り・更新・削除）のAPIを定義しています。
#
# 【サービス層パターン（Service Layer Pattern）について】
# エンドポイント（API）は直接データベースを操作せず、
# DatasetSvc（データセットサービス）を通じてビジネスロジックを実行します。
# これにより、コードの責任が分離され、テストや保守がしやすくなります。
#
# 【監査ログ（Audit Log）について】
# データの作成・エクスポート・削除など重要な操作を行った際に、
# AuditSvc（監査サービス）を使って「誰が・いつ・何をしたか」を記録します。
# これはセキュリティや運用管理のために重要です。
# =============================================================================

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

# AuditAction: 監査ログに記録するアクションの種類（作成、削除など）
from ....domain.entities.audit_log import AuditAction
# DatasetExportFormat: データセットのエクスポート形式（CSV、JSONなど）
from ....domain.entities.dataset import DatasetExportFormat
# AuditSvc: 監査ログサービス（操作履歴の記録を担当）
# CurrentUser: 現在ログイン中のユーザー情報（依存性注入で自動取得）
# DatasetSvc: データセット管理サービス（データセットの操作を担当）
from ..dependencies import AuditSvc, CurrentUser, DatasetSvc
# リクエスト/レスポンス用のスキーマ（データの型定義）
from ..schemas import DatasetCreate, DatasetExportRequest, DatasetResponse

# ルーターの作成: "/datasets" パスにマッピングされるAPIグループ
# tags=["datasets"] はAPIドキュメント（Swagger UI）での分類に使われます
router = APIRouter(prefix="/datasets", tags=["datasets"])


# =============================================================================
# データセット一覧取得 (GET /datasets)
# =============================================================================
# ログイン中のユーザーが所有するデータセットの一覧を返します。
# response_model=list[DatasetResponse] で、レスポンスの型を明示しています。
# =============================================================================
@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    current_user: CurrentUser,      # FastAPIの依存性注入で自動的にユーザー情報を取得
    dataset_svc: DatasetSvc,        # サービス層を通じてデータにアクセス
):
    # サービス層にユーザーIDを渡して、そのユーザーのデータセットを取得
    datasets = await dataset_svc.get_user_datasets(current_user.id)

    # 取得したデータセットをレスポンス用の形式に変換して返す
    # リスト内包表記を使って、各データセットをDatasetResponseに変換
    return [
        DatasetResponse(
            id=d.id,
            name=d.name,
            description=d.description,
            owner_id=d.owner_id,
            status=d.status.value,          # Enumの値を文字列に変換
            sensor_types=d.sensor_types,    # 使用しているセンサーの種類
            robot_ids=d.robot_ids,          # 関連するロボットのID一覧
            start_time=d.start_time,        # データ収集の開始時刻
            end_time=d.end_time,            # データ収集の終了時刻
            record_count=d.record_count,    # レコード数
            size_bytes=d.size_bytes,        # データサイズ（バイト単位）
            tags=d.tags,                    # 分類用のタグ
            created_at=d.created_at,        # 作成日時
        )
        for d in datasets
    ]


# =============================================================================
# データセット作成 (POST /datasets)
# =============================================================================
# 新しいデータセットを作成します。
# status_code=201 は「リソースが正常に作成された」を意味するHTTPステータスコードです。
# 作成後、監査ログにも記録します。
# =============================================================================
@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    body: DatasetCreate,            # リクエストボディ（作成に必要な情報）
    current_user: CurrentUser,      # 現在のユーザー（データセットの所有者になる）
    dataset_svc: DatasetSvc,        # データセットサービス
    audit_svc: AuditSvc,           # 監査ログサービス
):
    # サービス層を通じてデータセットを作成
    dataset = await dataset_svc.create_dataset(
        name=body.name,
        description=body.description,
        owner_id=current_user.id,
        robot_ids=body.robot_ids,
        sensor_types=body.sensor_types,
        start_time=body.start_time,
        end_time=body.end_time,
        tags=body.tags,
    )

    # 監査ログに「データセット作成」アクションを記録
    # これにより、誰がいつデータセットを作成したか追跡できます
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DATASET_CREATE,
        resource_type="dataset",
        resource_id=str(dataset.id),
    )

    # 作成されたデータセットをレスポンス形式に変換して返す
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        owner_id=dataset.owner_id,
        status=dataset.status.value,
        sensor_types=dataset.sensor_types,
        robot_ids=dataset.robot_ids,
        start_time=dataset.start_time,
        end_time=dataset.end_time,
        record_count=dataset.record_count,
        size_bytes=dataset.size_bytes,
        tags=dataset.tags,
        created_at=dataset.created_at,
    )


# =============================================================================
# データセット個別取得 (GET /datasets/{dataset_id})
# =============================================================================
# 指定されたIDのデータセットを1件取得します。
# 見つからない場合は404エラー（Not Found）を返します。
# =============================================================================
@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,               # URLパスから取得するデータセットID
    current_user: CurrentUser,
    dataset_svc: DatasetSvc,
):
    # サービス層を通じてデータセットを取得
    dataset = await dataset_svc.get_dataset(dataset_id)

    # データセットが見つからない場合、404エラーを返す
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # レスポンス形式に変換して返す
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        owner_id=dataset.owner_id,
        status=dataset.status.value,
        sensor_types=dataset.sensor_types,
        robot_ids=dataset.robot_ids,
        start_time=dataset.start_time,
        end_time=dataset.end_time,
        record_count=dataset.record_count,
        size_bytes=dataset.size_bytes,
        tags=dataset.tags,
        created_at=dataset.created_at,
    )


# =============================================================================
# データセットエクスポート (POST /datasets/{dataset_id}/export)
# =============================================================================
# データセットを指定された形式（CSV、JSONなど）でエクスポート（書き出し）します。
#
# 【エクスポートのフォーマットバリデーション】
# リクエストで指定された形式が有効かどうかをチェックし、
# 無効な形式の場合は400エラー（Bad Request）を返します。
# =============================================================================
@router.post("/{dataset_id}/export")
async def export_dataset(
    dataset_id: UUID,
    body: DatasetExportRequest,     # エクスポート設定（形式など）
    current_user: CurrentUser,
    dataset_svc: DatasetSvc,
    audit_svc: AuditSvc,
):
    # エクスポート形式のバリデーション（検証）
    # body.formatの値がDatasetExportFormatに定義された有効な形式か確認
    try:
        fmt = DatasetExportFormat(body.format)
    except ValueError:
        # サポートされていない形式の場合、400エラーを返す
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {body.format}",
        )

    # サービス層を通じてエクスポートを実行
    # 成功するとエクスポートされたファイルのパスが返される
    try:
        path = await dataset_svc.export_dataset(dataset_id, fmt)
    except ValueError as e:
        # データセットが見つからないなどのエラー
        raise HTTPException(status_code=400, detail=str(e))

    # 監査ログに「データセットエクスポート」アクションを記録
    # details にエクスポート形式も記録しておく
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DATASET_EXPORT,
        resource_type="dataset",
        resource_id=str(dataset_id),
        details={"format": body.format},
    )

    # エクスポートされたファイルのパスと形式を返す
    return {"path": path, "format": body.format}


# =============================================================================
# データセット削除 (DELETE /datasets/{dataset_id})
# =============================================================================
# 指定されたIDのデータセットを削除します。
# status_code=204 は「成功したがレスポンスボディは空」を意味します。
# 見つからない場合は404エラーを返します。
# =============================================================================
@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    current_user: CurrentUser,
    dataset_svc: DatasetSvc,
    audit_svc: AuditSvc,
):
    # サービス層を通じてデータセットを削除
    # 削除成功ならTrue、見つからなければFalseが返る
    deleted = await dataset_svc.delete_dataset(dataset_id)

    # データセットが見つからない場合、404エラーを返す
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 監査ログに「データセット削除」アクションを記録
    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DATASET_DELETE,
        resource_type="dataset",
        resource_id=str(dataset_id),
    )
