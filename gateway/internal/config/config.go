package config

import (
	"time"

	"github.com/spf13/viper"
)

// Config holds all gateway configuration
type Config struct {
	Server  ServerConfig
	Redis   RedisConfig
	Safety  SafetyConfig
	Auth    AuthConfig
	Logging LoggingConfig
}

type ServerConfig struct {
	Port     int    `mapstructure:"port"`
	GRPCPort int    `mapstructure:"grpc_port"`
	Host     string `mapstructure:"host"`
}

type RedisConfig struct {
	URL string `mapstructure:"url"`
}

type SafetyConfig struct {
	EStopEnabled            bool    `mapstructure:"estop_enabled"`
	CommandTimeoutSec       int     `mapstructure:"cmd_timeout_sec"`
	MaxLinearVelocity       float64 `mapstructure:"max_linear_vel"`
	MaxAngularVelocity      float64 `mapstructure:"max_angular_vel"`
	OperationLockTimeoutSec int     `mapstructure:"operation_lock_timeout_sec"`
}

type AuthConfig struct {
	JWTPublicKeyPath string `mapstructure:"jwt_public_key_path"`
}

type LoggingConfig struct {
	Level string `mapstructure:"level"`
}

// CommandTimeout returns the command timeout as a time.Duration
func (s *SafetyConfig) CommandTimeout() time.Duration {
	return time.Duration(s.CommandTimeoutSec) * time.Second
}

// OperationLockTimeout returns the operation lock timeout as a time.Duration
func (s *SafetyConfig) OperationLockTimeout() time.Duration {
	return time.Duration(s.OperationLockTimeoutSec) * time.Second
}

// Load reads configuration from environment variables
func Load() (*Config, error) {
	v := viper.New()
	v.AutomaticEnv()

	// Server defaults
	v.SetDefault("GATEWAY_PORT", 8080)
	v.SetDefault("GATEWAY_GRPC_PORT", 50051)
	v.SetDefault("GATEWAY_HOST", "0.0.0.0")

	// Safety defaults
	v.SetDefault("GATEWAY_ESTOP_ENABLED", true)
	v.SetDefault("GATEWAY_CMD_TIMEOUT_SEC", 3)
	v.SetDefault("GATEWAY_MAX_LINEAR_VEL", 1.0)
	v.SetDefault("GATEWAY_MAX_ANGULAR_VEL", 2.0)
	v.SetDefault("GATEWAY_OPERATION_LOCK_TIMEOUT_SEC", 300)

	// Auth defaults
	v.SetDefault("JWT_PUBLIC_KEY_PATH", "/app/keys/public.pem")

	// Logging defaults
	v.SetDefault("GATEWAY_LOG_LEVEL", "info")

	// Redis
	v.SetDefault("REDIS_URL", "redis://localhost:6379/0")

	cfg := &Config{
		Server: ServerConfig{
			Port:     v.GetInt("GATEWAY_PORT"),
			GRPCPort: v.GetInt("GATEWAY_GRPC_PORT"),
			Host:     v.GetString("GATEWAY_HOST"),
		},
		Redis: RedisConfig{
			URL: v.GetString("REDIS_URL"),
		},
		Safety: SafetyConfig{
			EStopEnabled:            v.GetBool("GATEWAY_ESTOP_ENABLED"),
			CommandTimeoutSec:       v.GetInt("GATEWAY_CMD_TIMEOUT_SEC"),
			MaxLinearVelocity:       v.GetFloat64("GATEWAY_MAX_LINEAR_VEL"),
			MaxAngularVelocity:      v.GetFloat64("GATEWAY_MAX_ANGULAR_VEL"),
			OperationLockTimeoutSec: v.GetInt("GATEWAY_OPERATION_LOCK_TIMEOUT_SEC"),
		},
		Auth: AuthConfig{
			JWTPublicKeyPath: v.GetString("JWT_PUBLIC_KEY_PATH"),
		},
		Logging: LoggingConfig{
			Level: v.GetString("GATEWAY_LOG_LEVEL"),
		},
	}

	return cfg, nil
}
