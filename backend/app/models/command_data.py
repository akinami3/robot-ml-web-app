"""
Command Data Model - for ML training data (control actions)

Frontend -> Gateway 方向のコマンド（制御値）を記録する。
sensor_data_records のセンサ値と合わせて
(state, action) ペアを構成し、模倣学習・強化学習の教師データとして利用する。
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, Index
from sqlalchemy.sql import func

from app.models.models import Base


class CommandDataRecord(Base):
    """
    Command data recorded from operator actions for ML training.
    
    MLでの用途:
    - 模倣学習: (sensor_state, command) ペアで教師データ
    - 逆強化学習: (state_before, command, state_after) のトランジション
    - 異常検知: コマンドパターンの異常検出
    - 経路最適化: 時系列コマンドの分析
    """
    __tablename__ = "command_data_records"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(String(50), index=True, nullable=False)
    
    # コマンド送信時刻 (Gateway側のタイムスタンプ)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    
    # コマンド情報
    command = Column(String(50), nullable=False)  # move, stop, pause, resume, etc.
    parameters = Column(JSON, nullable=False, default={})  # {x, y, speed, ...}
    
    # 操作者情報
    user_id = Column(String(100), nullable=True)
    
    # 実行結果
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(String(500), nullable=True)
    
    # コマンド実行前のロボット状態 (ML用: state-action ペア)
    robot_state_before = Column(JSON, nullable=False, default={})  # {x, y, theta, battery, ...}
    
    # メタデータ
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_command_data_robot_time', 'robot_id', 'recorded_at'),
        Index('idx_command_data_user', 'user_id', 'recorded_at'),
        Index('idx_command_data_command', 'command', 'recorded_at'),
    )
