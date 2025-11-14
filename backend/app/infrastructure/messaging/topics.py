"""MQTT topic templates and helper utilities."""

VELOCITY_COMMAND_TOPIC_TEMPLATE = "/amr/{robot_id}/cmd_vel"
NAVIGATION_COMMAND_TOPIC_TEMPLATE = "/amr/{robot_id}/navigation_goal"
TELEMETRY_SUBSCRIPTION_PATTERN = "/amr/+/telemetry/#"


def velocity_command_topic(robot_id: str) -> str:
    """Generate the velocity command topic for a specific robot."""
    return VELOCITY_COMMAND_TOPIC_TEMPLATE.format(robot_id=robot_id)


def navigation_command_topic(robot_id: str) -> str:
    """Generate the navigation command topic for a specific robot."""
    return NAVIGATION_COMMAND_TOPIC_TEMPLATE.format(robot_id=robot_id)
