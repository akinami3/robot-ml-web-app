"""Dataset management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ....domain.entities.audit_log import AuditAction
from ....domain.entities.dataset import DatasetExportFormat
from ..dependencies import AuditSvc, CurrentUser, DatasetSvc
from ..schemas import DatasetCreate, DatasetExportRequest, DatasetResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    current_user: CurrentUser,
    dataset_svc: DatasetSvc,
):
    datasets = await dataset_svc.get_user_datasets(current_user.id)
    return [
        DatasetResponse(
            id=d.id,
            name=d.name,
            description=d.description,
            owner_id=d.owner_id,
            status=d.status.value,
            sensor_types=d.sensor_types,
            robot_ids=d.robot_ids,
            start_time=d.start_time,
            end_time=d.end_time,
            record_count=d.record_count,
            size_bytes=d.size_bytes,
            tags=d.tags,
            created_at=d.created_at,
        )
        for d in datasets
    ]


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    body: DatasetCreate,
    current_user: CurrentUser,
    dataset_svc: DatasetSvc,
    audit_svc: AuditSvc,
):
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

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DATASET_CREATE,
        resource_type="dataset",
        resource_id=str(dataset.id),
    )

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


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    current_user: CurrentUser,
    dataset_svc: DatasetSvc,
):
    dataset = await dataset_svc.get_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

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


@router.post("/{dataset_id}/export")
async def export_dataset(
    dataset_id: UUID,
    body: DatasetExportRequest,
    current_user: CurrentUser,
    dataset_svc: DatasetSvc,
    audit_svc: AuditSvc,
):
    try:
        fmt = DatasetExportFormat(body.format)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {body.format}",
        )

    try:
        path = await dataset_svc.export_dataset(dataset_id, fmt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DATASET_EXPORT,
        resource_type="dataset",
        resource_id=str(dataset_id),
        details={"format": body.format},
    )

    return {"path": path, "format": body.format}


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    current_user: CurrentUser,
    dataset_svc: DatasetSvc,
    audit_svc: AuditSvc,
):
    deleted = await dataset_svc.delete_dataset(dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.DATASET_DELETE,
        resource_type="dataset",
        resource_id=str(dataset_id),
    )
