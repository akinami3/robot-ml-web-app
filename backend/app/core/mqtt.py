"""
MQTT client connection and management
"""
import asyncio
import json
from typing import Any, Callable, Dict, Optional

import paho.mqtt.client as mqtt
from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)


class MQTTClient:
    """MQTT Client for robot communication"""

    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected: bool = False
        self.message_handlers: Dict[str, Callable] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self) -> None:
        """Connect to MQTT broker"""
        try:
            self.loop = asyncio.get_event_loop()
            self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)

            # Set authentication if provided
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Connect to broker
            self.client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                settings.MQTT_KEEPALIVE,
            )

            # Start network loop in background
            self.client.loop_start()

            logger.info(
                "mqtt_connecting",
                broker=settings.MQTT_BROKER_HOST,
                port=settings.MQTT_BROKER_PORT,
            )

        except Exception as e:
            logger.error("mqtt_connect_error", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("mqtt_disconnected")

    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            logger.info("mqtt_connected", result_code=rc)

            # Subscribe to robot topics
            topics = [
                settings.MQTT_TOPIC_ROBOT_STATUS,
                settings.MQTT_TOPIC_CAMERA_IMAGE,
                settings.MQTT_TOPIC_NAV_STATUS,
            ]
            for topic in topics:
                self.client.subscribe(topic, qos=1)
                logger.debug("mqtt_subscribed", topic=topic)
        else:
            logger.error("mqtt_connection_failed", result_code=rc)

    def _on_disconnect(self, client, userdata, rc) -> None:
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        logger.warning("mqtt_disconnected", result_code=rc)

    def _on_message(self, client, userdata, msg) -> None:
        """Callback when message received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())

            logger.debug("mqtt_message_received", topic=topic, payload=payload)

            # Call registered handler if exists
            if topic in self.message_handlers:
                handler = self.message_handlers[topic]
                if self.loop:
                    asyncio.run_coroutine_threadsafe(handler(payload), self.loop)

        except Exception as e:
            logger.error("mqtt_message_error", error=str(e), topic=msg.topic)

    def register_handler(self, topic: str, handler: Callable) -> None:
        """
        Register message handler for specific topic

        Args:
            topic: MQTT topic
            handler: Async function to handle messages
        """
        self.message_handlers[topic] = handler
        logger.debug("mqtt_handler_registered", topic=topic)

    async def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1) -> None:
        """
        Publish message to MQTT topic

        Args:
            topic: MQTT topic
            payload: Message payload (will be converted to JSON)
            qos: Quality of Service level (0, 1, or 2)
        """
        if not self.connected:
            logger.warning("mqtt_not_connected", topic=topic)
            return

        try:
            message = json.dumps(payload)
            result = self.client.publish(topic, message, qos=qos)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug("mqtt_message_published", topic=topic, payload=payload)
            else:
                logger.error("mqtt_publish_failed", topic=topic, result_code=result.rc)

        except Exception as e:
            logger.error("mqtt_publish_error", error=str(e), topic=topic)


# Global MQTT client instance
mqtt_client = MQTTClient()
