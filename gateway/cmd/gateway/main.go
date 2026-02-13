package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"github.com/robot-ai-webapp/gateway/internal/adapter/mock"
	"github.com/robot-ai-webapp/gateway/internal/bridge"
	"github.com/robot-ai-webapp/gateway/internal/config"
	mw "github.com/robot-ai-webapp/gateway/internal/middleware"
	"github.com/robot-ai-webapp/gateway/internal/protocol"
	"github.com/robot-ai-webapp/gateway/internal/safety"
	"github.com/robot-ai-webapp/gateway/internal/server"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to load config: %v\n", err)
		os.Exit(1)
	}

	// Initialize logger
	logger := initLogger(cfg.Logging.Level)
	defer logger.Sync()

	logger.Info("Starting Robot AI Gateway",
		zap.Int("ws_port", cfg.Server.Port),
		zap.Int("grpc_port", cfg.Server.GRPCPort),
	)

	// Initialize Redis publisher
	redisPublisher, err := bridge.NewRedisPublisher(cfg.Redis.URL, logger)
	if err != nil {
		logger.Warn("Redis connection failed, running without persistence", zap.Error(err))
		redisPublisher = nil
	}

	// Initialize adapter registry
	registry := adapter.NewRegistry(logger)
	registry.RegisterFactory("mock", mock.Factory)

	// Initialize safety components
	estopMgr := safety.NewEStopManager(registry, logger)
	velLimiter := safety.NewVelocityLimiter(cfg.Safety.MaxLinearVelocity, cfg.Safety.MaxAngularVelocity, logger)
	opLock := safety.NewOperationLock(cfg.Safety.OperationLockTimeout(), logger)
	watchdog := safety.NewTimeoutWatchdog(cfg.Safety.CommandTimeout(), registry, logger)

	// Initialize hub and handler
	hub := server.NewHub(logger)
	go hub.Run()

	// Create handler with appropriate publisher interface
	var publisher server.RedisPublisher
	if redisPublisher != nil {
		publisher = redisPublisher
	}

	handler := server.NewHandler(hub, registry, estopMgr, velLimiter, watchdog, opLock, publisher, logger)
	wsServer := server.NewWebSocketServer(hub, handler, logger)

	// Start watchdog
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	watchdog.Start(ctx)

	// Start operation lock cleanup
	done := make(chan struct{})
	opLock.StartCleanup(done)

	// Create and connect mock robot for development
	mockAdapter, err := registry.CreateAdapter("mock-robot-1", "mock")
	if err != nil {
		logger.Fatal("Failed to create mock adapter", zap.Error(err))
	}
	if err := mockAdapter.Connect(ctx, nil); err != nil {
		logger.Fatal("Failed to connect mock adapter", zap.Error(err))
	}

	// Start sensor data forwarding goroutine
	codec := protocol.NewCodec()
	go forwardSensorData(ctx, "mock-robot-1", mockAdapter, hub, codec, redisPublisher, logger)

	// Setup HTTP server
	rateLimiter := mw.NewRateLimiter(120, logger)
	mux := http.NewServeMux()
	mux.HandleFunc("/ws", wsServer.HandleWebSocket)
	mux.HandleFunc("/health", wsServer.HealthHandler)
	mux.HandleFunc("/ready", wsServer.HealthHandler)

	httpServer := &http.Server{
		Addr:         fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port),
		Handler:      rateLimiter.Middleware(mw.LoggingMiddleware(logger)(mux)),
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server
	go func() {
		logger.Info("WebSocket server starting", zap.String("addr", httpServer.Addr))
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("Server failed", zap.Error(err))
		}
	}()

	// Graceful shutdown
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	logger.Info("Shutting down gracefully...")

	// Cancel context to stop background goroutines
	cancel()
	close(done)

	// Disconnect mock adapter
	_ = mockAdapter.Disconnect(context.Background())

	// Close Redis
	if redisPublisher != nil {
		_ = redisPublisher.Close()
	}

	// Shutdown HTTP server
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()
	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		logger.Error("Server shutdown error", zap.Error(err))
	}

	logger.Info("Gateway stopped")
}

func forwardSensorData(
	ctx context.Context,
	robotID string,
	adp adapter.RobotAdapter,
	hub *server.Hub,
	codec *protocol.Codec,
	redisPublisher *bridge.RedisPublisher,
	logger *zap.Logger,
) {
	ch := adp.SensorDataChannel()
	for {
		select {
		case <-ctx.Done():
			return
		case data, ok := <-ch:
			if !ok {
				return
			}

			data.RobotID = robotID

			// Forward to WebSocket clients
			msg := protocol.NewMessage(protocol.MsgTypeSensorData, robotID)
			msg.Topic = data.Topic
			msg.Payload = map[string]any{
				"data_type": data.DataType,
				"frame_id":  data.FrameID,
				"data":      data.Data,
			}

			encoded, err := codec.Encode(msg)
			if err != nil {
				logger.Error("Failed to encode sensor data", zap.Error(err))
				continue
			}
			hub.BroadcastToRobot(robotID, encoded)

			// Publish to Redis for backend recording
			if redisPublisher != nil {
				_ = redisPublisher.PublishSensorData(ctx, robotID, data)
			}
		}
	}
}

func initLogger(level string) *zap.Logger {
	var zapLevel zapcore.Level
	switch level {
	case "debug":
		zapLevel = zapcore.DebugLevel
	case "info":
		zapLevel = zapcore.InfoLevel
	case "warn":
		zapLevel = zapcore.WarnLevel
	case "error":
		zapLevel = zapcore.ErrorLevel
	default:
		zapLevel = zapcore.InfoLevel
	}

	config := zap.Config{
		Level:            zap.NewAtomicLevelAt(zapLevel),
		Development:      zapLevel == zapcore.DebugLevel,
		Encoding:         "json",
		EncoderConfig:    zap.NewProductionEncoderConfig(),
		OutputPaths:      []string{"stdout"},
		ErrorOutputPaths: []string{"stderr"},
	}
	config.EncoderConfig.TimeKey = "timestamp"
	config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	logger, err := config.Build()
	if err != nil {
		panic(err)
	}
	return logger
}
