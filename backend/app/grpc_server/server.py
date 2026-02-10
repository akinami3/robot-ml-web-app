"""
gRPC Server for Data Recording

Gateway -> Backend へのセンサデータ記録を受け付けるgRPCサーバー
"""
import grpc
from concurrent import futures
from datetime import datetime, timezone
import logging

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.sensor_data import SensorDataRecord

logger = logging.getLogger(__name__)

# Import generated protobuf code
try:
    from app.grpc_client import fleet_pb2, fleet_pb2_grpc
    _PROTO_AVAILABLE = True
except ImportError:
    logger.warning("Proto files not generated. Run: python -m grpc_tools.protoc ...")
    fleet_pb2 = None
    fleet_pb2_grpc = None
    _PROTO_AVAILABLE = False

# Base class for DataRecordingServer
_base_class = (
    fleet_pb2_grpc.DataRecordingServiceServicer
    if _PROTO_AVAILABLE
    else object
)


class DataRecordingServer(_base_class):
    """Handles sensor data recording from Gateway"""

    async def RecordSensorData(self, request, context):
        """Receive a batch of sensor data records and store in DB"""
        recorded_count = 0

        try:
            async with AsyncSessionLocal() as session:
                for record in request.records:
                    db_record = SensorDataRecord(
                        robot_id=record.robot_id,
                        recorded_at=datetime.fromtimestamp(
                            record.timestamp / 1000.0, tz=timezone.utc
                        ),
                        sensor_data=dict(record.sensor_data),
                        control_data=dict(record.control_data),
                    )
                    session.add(db_record)
                    recorded_count += 1

                await session.commit()

            logger.info(f"Recorded {recorded_count} sensor data entries")
            return fleet_pb2.BatchSensorDataResponse(
                success=True,
                recorded_count=recorded_count,
                message=f"Recorded {recorded_count} entries",
            )
        except Exception as e:
            logger.error(f"Failed to record sensor data: {e}")
            return fleet_pb2.BatchSensorDataResponse(
                success=False,
                recorded_count=0,
                message=str(e),
            )

    async def StreamSensorData(self, request_iterator, context):
        """Receive streaming sensor data and store in DB"""
        recorded_count = 0
        batch = []
        batch_size = 50

        try:
            async for record in request_iterator:
                batch.append(
                    SensorDataRecord(
                        robot_id=record.robot_id,
                        recorded_at=datetime.fromtimestamp(
                            record.timestamp / 1000.0, tz=timezone.utc
                        ),
                        sensor_data=dict(record.sensor_data),
                        control_data=dict(record.control_data),
                    )
                )

                if len(batch) >= batch_size:
                    async with AsyncSessionLocal() as session:
                        session.add_all(batch)
                        await session.commit()
                    recorded_count += len(batch)
                    batch = []

            # Flush remaining
            if batch:
                async with AsyncSessionLocal() as session:
                    session.add_all(batch)
                    await session.commit()
                recorded_count += len(batch)

            logger.info(f"Stream recorded {recorded_count} sensor data entries")
            return fleet_pb2.BatchSensorDataResponse(
                success=True,
                recorded_count=recorded_count,
                message=f"Streamed {recorded_count} entries",
            )
        except Exception as e:
            logger.error(f"Failed to stream sensor data: {e}")
            return fleet_pb2.BatchSensorDataResponse(
                success=False,
                recorded_count=recorded_count,
                message=str(e),
            )


async def start_grpc_server(port: int = None):
    """Start the gRPC server for data recording"""
    if not _PROTO_AVAILABLE:
        logger.error("Cannot start gRPC server: proto files not generated")
        return

    port = port or settings.GRPC_SERVER_PORT
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    fleet_pb2_grpc.add_DataRecordingServiceServicer_to_server(
        DataRecordingServer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    logger.info(f"Data recording gRPC server started on port {port}")
    await server.wait_for_termination()
