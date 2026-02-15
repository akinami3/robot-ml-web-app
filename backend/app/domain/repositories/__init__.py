# ============================================================
# リポジトリパッケージの公開インターフェース（__init__.py）
# ============================================================
# __init__.py は Python パッケージの「入り口」ファイルです。
#
# 【__all__ の役割】
# from repositories import * とインポートしたときに、
# 外部に公開するクラス名を明示的に指定します。
# これにより、パッケージの利用者は必要なリポジトリを
# 簡単にインポートできます。
#
# 使用例:
#   from app.domain.repositories import UserRepository, RobotRepository
# ============================================================

# 抽象基底クラス（全リポジトリの親クラス）
from .base import BaseRepository
# 各エンティティ固有のリポジトリインターフェース
from .user_repository import UserRepository
from .robot_repository import RobotRepository
from .sensor_data_repository import SensorDataRepository
from .dataset_repository import DatasetRepository
from .rag_repository import RAGRepository
from .audit_repository import AuditRepository
from .recording_repository import RecordingRepository

# __all__: このパッケージから外部に公開するクラス名のリスト
# 「from repositories import *」した時にこのリストのクラスだけがインポートされる
__all__ = [
    "BaseRepository",        # 基底クラス
    "UserRepository",        # ユーザー
    "RobotRepository",       # ロボット
    "SensorDataRepository",  # センサーデータ
    "DatasetRepository",     # データセット
    "RAGRepository",         # RAG（検索拡張生成）
    "AuditRepository",       # 監査ログ
    "RecordingRepository",   # 録画セッション
]
