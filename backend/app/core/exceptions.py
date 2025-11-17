"""
Custom exceptions for the application
"""


class RobotMLException(Exception):
    """Base exception for Robot ML application"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseException(RobotMLException):
    """Database related exceptions"""

    def __init__(self, message: str = "Database error occurred"):
        super().__init__(message, status_code=500)


class MQTTException(RobotMLException):
    """MQTT related exceptions"""

    def __init__(self, message: str = "MQTT communication error"):
        super().__init__(message, status_code=503)


class RobotControlException(RobotMLException):
    """Robot control related exceptions"""

    def __init__(self, message: str = "Robot control error"):
        super().__init__(message, status_code=500)


class RecordingException(RobotMLException):
    """Data recording related exceptions"""

    def __init__(self, message: str = "Recording error"):
        super().__init__(message, status_code=500)


class MLException(RobotMLException):
    """Machine learning related exceptions"""

    def __init__(self, message: str = "Machine learning error"):
        super().__init__(message, status_code=500)


class ModelNotFoundException(MLException):
    """Model not found exception"""

    def __init__(self, model_id: str):
        super().__init__(f"Model not found: {model_id}", status_code=404)


class DatasetNotFoundException(RobotMLException):
    """Dataset not found exception"""

    def __init__(self, dataset_id: str):
        super().__init__(f"Dataset not found: {dataset_id}", status_code=404)


class ChatbotException(RobotMLException):
    """Chatbot related exceptions"""

    def __init__(self, message: str = "Chatbot error"):
        super().__init__(message, status_code=500)


class SimulatorException(RobotMLException):
    """Unity simulator related exceptions"""

    def __init__(self, message: str = "Simulator error"):
        super().__init__(message, status_code=500)


class ValidationException(RobotMLException):
    """Validation error exception"""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)
