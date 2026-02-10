package config

import (
	"os"
	"strconv"
)

// Config holds the application configuration
type Config struct {
	// gRPC Server (FleetGateway service)
	GRPCPort string
	Debug    bool

	// WebSocket Server (Frontend direct communication)
	WebSocketPort string
	JWTSecret     string

	// MQTT (Robot communication)
	MQTTBrokerHost  string
	MQTTBrokerPort  int
	MQTTClientID    string
	MQTTTopicPrefix string

	// Backend gRPC (data recording destination)
	BackendGRPCAddress string

	// Redis (caching)
	RedisURL string
}

// Load loads configuration from environment variables
func Load() *Config {
	return &Config{
		GRPCPort:           getEnv("GRPC_PORT", "50051"),
		Debug:              getEnvBool("DEBUG", false),
		WebSocketPort:      getEnv("WEBSOCKET_PORT", "8082"),
		JWTSecret:          getEnv("JWT_SECRET_KEY", "your-super-secret-key"),
		MQTTBrokerHost:     getEnv("MQTT_BROKER_HOST", "mqtt-broker"),
		MQTTBrokerPort:     getEnvInt("MQTT_BROKER_PORT", 1883),
		MQTTClientID:       getEnv("MQTT_CLIENT_ID", "fleet-gateway"),
		MQTTTopicPrefix:    getEnv("MQTT_TOPIC_PREFIX", "amr/"),
		BackendGRPCAddress: getEnv("BACKEND_GRPC_ADDRESS", "backend:50052"),
		RedisURL:           getEnv("REDIS_URL", "redis://redis:6379/0"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}
