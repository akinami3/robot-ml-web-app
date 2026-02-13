package bridge

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/redis/go-redis/v9"
	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"go.uber.org/zap"
)

const (
	sensorDataStream = "robot:sensor_data"
	commandStream    = "robot:commands"
)

// RedisPublisher publishes sensor data and commands to Redis Streams
type RedisPublisher struct {
	client *redis.Client
	logger *zap.Logger
}

// NewRedisPublisher creates a new Redis publisher
func NewRedisPublisher(redisURL string, logger *zap.Logger) (*RedisPublisher, error) {
	opts, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, fmt.Errorf("invalid redis URL: %w", err)
	}

	client := redis.NewClient(opts)

	// Test connection
	if err := client.Ping(context.Background()).Err(); err != nil {
		return nil, fmt.Errorf("redis connection failed: %w", err)
	}

	logger.Info("Connected to Redis")

	return &RedisPublisher{
		client: client,
		logger: logger,
	}, nil
}

// PublishSensorData publishes sensor data to the sensor data stream
func (r *RedisPublisher) PublishSensorData(ctx context.Context, robotID string, data adapter.SensorData) error {
	payload, err := json.Marshal(data.Data)
	if err != nil {
		return err
	}

	return r.client.XAdd(ctx, &redis.XAddArgs{
		Stream: sensorDataStream,
		MaxLen: 100000, // Keep last 100K entries
		Approx: true,
		Values: map[string]interface{}{
			"robot_id":  robotID,
			"topic":     data.Topic,
			"data_type": data.DataType,
			"frame_id":  data.FrameID,
			"timestamp": data.Timestamp,
			"payload":   string(payload),
		},
	}).Err()
}

// PublishCommand publishes a command to the command stream
func (r *RedisPublisher) PublishCommand(ctx context.Context, robotID string, cmd adapter.Command) error {
	payload, err := json.Marshal(cmd.Payload)
	if err != nil {
		return err
	}

	return r.client.XAdd(ctx, &redis.XAddArgs{
		Stream: commandStream,
		MaxLen: 50000,
		Approx: true,
		Values: map[string]interface{}{
			"robot_id":  robotID,
			"type":      cmd.Type,
			"timestamp": cmd.Timestamp,
			"payload":   string(payload),
		},
	}).Err()
}

// Close closes the Redis connection
func (r *RedisPublisher) Close() error {
	return r.client.Close()
}
