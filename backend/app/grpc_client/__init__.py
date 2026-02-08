"""
gRPC Client for Fleet Gateway communication
"""

from .client import FleetGatewayClient, get_gateway_client, gateway_client_context
from . import fleet_pb2

__all__ = [
    "FleetGatewayClient",
    "get_gateway_client", 
    "gateway_client_context",
    "fleet_pb2",
]
