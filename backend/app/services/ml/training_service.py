"""
ML Training Service

Handles machine learning model training operations
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

import structlog
import torch
import torch.nn as nn
import torch.optim as optim
from sqlalchemy.ext.asyncio import AsyncSession
from torch.utils.data import DataLoader

from app.config import settings
from app.core.exceptions import MLException
from app.core.websocket import ConnectionManager
from app.repositories.dataset import DatasetRepository
from app.repositories.ml_model import MLModelRepository, TrainingHistoryRepository
from app.schemas.ml import TrainingConfig, TrainingStatus

logger = structlog.get_logger(__name__)


class TrainingService:
    """Service for ML model training"""

    def __init__(self, ws_manager: ConnectionManager):
        self.ws_manager = ws_manager
        self.active_trainings: Dict[UUID, asyncio.Task] = {}
        self.training_status: Dict[UUID, TrainingStatus] = {}

    async def start_training(
        self,
        db: AsyncSession,
        model_id: UUID,
        config: TrainingConfig,
    ) -> Dict:
        """
        Start model training
        
        Args:
            db: Database session
            model_id: ML model ID
            config: Training configuration
            
        Returns:
            Status dictionary
        """
        try:
            # Check if already training
            if model_id in self.active_trainings:
                raise MLException(f"Model {model_id} is already training")

            # Get model from database
            model_repo = MLModelRepository(db)
            ml_model = await model_repo.get(model_id)
            if not ml_model:
                raise MLException(f"Model {model_id} not found")

            # Get dataset
            dataset_repo = DatasetRepository(db)
            dataset = await dataset_repo.get(config.dataset_id)
            if not dataset:
                raise MLException(f"Dataset {config.dataset_id} not found")

            # Update model status
            await model_repo.update(model_id, {"status": "training"})
            await db.commit()

            # Start training in background task
            task = asyncio.create_task(
                self._train_model(db, ml_model, dataset, config)
            )
            self.active_trainings[model_id] = task

            logger.info(f"Started training for model {model_id}")

            return {
                "status": "started",
                "model_id": str(model_id),
                "message": "Training started successfully"
            }

        except Exception as e:
            logger.error(f"Failed to start training: {e}")
            raise MLException(f"Failed to start training: {e}")

    async def stop_training(self, db: AsyncSession, model_id: UUID) -> Dict:
        """
        Stop active training
        
        Args:
            db: Database session
            model_id: ML model ID
            
        Returns:
            Status dictionary
        """
        try:
            if model_id not in self.active_trainings:
                raise MLException(f"No active training for model {model_id}")

            # Cancel training task
            task = self.active_trainings[model_id]
            task.cancel()

            # Wait for cancellation
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Update model status
            model_repo = MLModelRepository(db)
            await model_repo.update(model_id, {"status": "stopped"})
            await db.commit()

            # Clean up
            del self.active_trainings[model_id]
            if model_id in self.training_status:
                del self.training_status[model_id]

            logger.info(f"Stopped training for model {model_id}")

            return {
                "status": "stopped",
                "model_id": str(model_id),
                "message": "Training stopped successfully"
            }

        except Exception as e:
            logger.error(f"Failed to stop training: {e}")
            raise MLException(f"Failed to stop training: {e}")

    async def get_training_status(
        self,
        model_id: UUID
    ) -> Optional[TrainingStatus]:
        """
        Get training status
        
        Args:
            model_id: ML model ID
            
        Returns:
            Training status or None
        """
        return self.training_status.get(model_id)

    async def _train_model(
        self,
        db: AsyncSession,
        ml_model,
        dataset,
        config: TrainingConfig
    ):
        """
        Internal training loop (runs in background)
        
        Args:
            db: Database session
            ml_model: ML model object
            dataset: Dataset object
            config: Training configuration
        """
        model_id = ml_model.id
        model_repo = MLModelRepository(db)
        history_repo = TrainingHistoryRepository(db)

        try:
            # Initialize status
            status = TrainingStatus(
                model_id=model_id,
                is_training=True,
                current_epoch=0,
                total_epochs=config.epochs,
                train_loss=0.0,
                val_loss=0.0,
                train_accuracy=0.0,
                val_accuracy=0.0,
                learning_rate=config.learning_rate,
            )
            self.training_status[model_id] = status

            # TODO: Load actual dataset and create data loaders
            # This is a placeholder - implement based on your data format
            logger.info(f"Loading dataset {dataset.id}")
            
            # Placeholder: Create dummy model and optimizer
            # Replace with actual model architecture
            model = nn.Sequential(
                nn.Linear(10, 64),
                nn.ReLU(),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Linear(32, 2)
            )
            
            if torch.cuda.is_available() and config.device == "cuda":
                model = model.cuda()
                device = torch.device("cuda")
            else:
                device = torch.device("cpu")

            optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)
            criterion = nn.CrossEntropyLoss()

            # Training loop
            for epoch in range(config.epochs):
                # Check if cancelled
                if model_id not in self.active_trainings:
                    logger.info(f"Training cancelled for model {model_id}")
                    break

                status.current_epoch = epoch + 1

                # Training phase
                model.train()
                train_loss = 0.0
                # TODO: Implement actual training with DataLoader
                
                # Validation phase
                model.eval()
                val_loss = 0.0
                # TODO: Implement actual validation
                
                # Update status
                status.train_loss = train_loss
                status.val_loss = val_loss
                # TODO: Calculate accuracies
                
                # Broadcast progress via WebSocket
                await self.ws_manager.broadcast_to_channel(
                    "ml",
                    {
                        "type": "training_progress",
                        "model_id": str(model_id),
                        "epoch": epoch + 1,
                        "train_loss": train_loss,
                        "val_loss": val_loss,
                    }
                )

                # Save training history
                history_data = {
                    "model_id": model_id,
                    "epoch": epoch + 1,
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "train_accuracy": 0.0,  # TODO: Calculate
                    "val_accuracy": 0.0,  # TODO: Calculate
                    "learning_rate": config.learning_rate,
                }
                await history_repo.create(history_data)
                await db.commit()

                # Early stopping check
                if config.early_stopping_patience:
                    # TODO: Implement early stopping logic
                    pass

                # Checkpoint saving
                if (epoch + 1) % 10 == 0:
                    checkpoint_path = self._save_checkpoint(
                        model, optimizer, epoch + 1, model_id
                    )
                    logger.info(f"Saved checkpoint: {checkpoint_path}")

                # Small delay to prevent blocking
                await asyncio.sleep(0.1)

            # Training completed
            # Save final model
            model_path = self._save_model(model, model_id)
            await model_repo.update(
                model_id,
                {
                    "status": "trained",
                    "model_path": str(model_path),
                    "last_trained_at": datetime.utcnow()
                }
            )
            await db.commit()

            # Update final status
            status.is_training = False
            
            # Broadcast completion
            await self.ws_manager.broadcast_to_channel(
                "ml",
                {
                    "type": "training_complete",
                    "model_id": str(model_id),
                    "final_train_loss": status.train_loss,
                    "final_val_loss": status.val_loss,
                }
            )

            logger.info(f"Training completed for model {model_id}")

        except asyncio.CancelledError:
            logger.info(f"Training cancelled for model {model_id}")
            await model_repo.update(model_id, {"status": "stopped"})
            await db.commit()
            raise

        except Exception as e:
            logger.error(f"Training failed for model {model_id}: {e}")
            await model_repo.update(
                model_id,
                {"status": "failed", "error_message": str(e)}
            )
            await db.commit()

            # Broadcast error
            await self.ws_manager.broadcast_to_channel(
                "ml",
                {
                    "type": "training_error",
                    "model_id": str(model_id),
                    "error": str(e)
                }
            )

        finally:
            # Clean up
            if model_id in self.active_trainings:
                del self.active_trainings[model_id]
            if model_id in self.training_status:
                del self.training_status[model_id]

    def _save_checkpoint(
        self,
        model: nn.Module,
        optimizer: optim.Optimizer,
        epoch: int,
        model_id: UUID
    ) -> Path:
        """Save training checkpoint"""
        checkpoint_dir = Path(settings.MODEL_STORAGE_PATH) / str(model_id) / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint_path = checkpoint_dir / f"checkpoint_epoch_{epoch}.pth"
        
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
        }, checkpoint_path)
        
        return checkpoint_path

    def _save_model(self, model: nn.Module, model_id: UUID) -> Path:
        """Save trained model"""
        model_dir = Path(settings.MODEL_STORAGE_PATH) / str(model_id)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = model_dir / "model.pth"
        torch.save(model.state_dict(), model_path)
        
        return model_path


# Global instance
_training_service: Optional[TrainingService] = None


def get_training_service(ws_manager: Optional[ConnectionManager] = None) -> TrainingService:
    """Get training service instance (singleton)"""
    global _training_service
    if _training_service is None:
        if ws_manager is None:
            raise ValueError("WebSocket manager required for first initialization")
        _training_service = TrainingService(ws_manager)
    return _training_service
