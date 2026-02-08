package config

import (
	"os"
	"strconv"
)

// Config holds the application configuration
type Config struct {
	// HTTP Server
	HTTPPort string
	Debug    bool

	// MQTT
	MQTTBrokerHost string
	MQTTBrokerPort int
	MQTTClientID   string
	MQTTTopicPrefix string

	// Backend
	BackendURL string

	// Redis
	RedisURL string
}

// Load loads configuration from environment variables
func Load() *Config {
	return &Config{
		HTTPPort:        getEnv("HTTP_PORT", "8080"),
		Debug:           getEnvBool("DEBUG", false),
		MQTTBrokerHost:  getEnv("MQTT_BROKER_HOST", "mqtt-broker"),
		MQTTBrokerPort:  getEnvInt("MQTT_BROKER_PORT", 1883),
		MQTTClientID:    getEnv("MQTT_CLIENT_ID", "fleet-gateway"),
		MQTTTopicPrefix: getEnv("MQTT_TOPIC_PREFIX", "amr/"),
		BackendURL:      getEnv("BACKEND_URL", "http://backend:8000"),
		RedisURL:        getEnv("REDIS_URL", "redis://redis:6379/0"),
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
