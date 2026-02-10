package main

import (
	"os"
	"os/signal"
	"syscall"

	"github.com/amr-saas/gateway/internal/config"
	"github.com/amr-saas/gateway/internal/forwarder"
	grpcserver "github.com/amr-saas/gateway/internal/grpc"
	"github.com/amr-saas/gateway/internal/mqtt"
	"github.com/amr-saas/gateway/internal/robot"
	"github.com/amr-saas/gateway/internal/websocket"
	"go.uber.org/zap"
)

func main() {
	// Initialize logger
	logger, _ := zap.NewProduction()
	defer logger.Sync()
	sugar := logger.Sugar()

	// Load configuration
	cfg := config.Load()

	// Initialize robot manager
	robotManager := robot.NewManager(sugar)

	// Initialize MQTT client
	mqttClient, err := mqtt.NewClient(cfg, robotManager, sugar)
	if err != nil {
		sugar.Fatalf("Failed to create MQTT client: %v", err)
	}

	// Connect to MQTT broker
	if err := mqttClient.Connect(); err != nil {
		sugar.Warnf("Failed to connect to MQTT broker: %v", err)
	} else {
		sugar.Info("Connected to MQTT broker")
	}

	// Initialize backend forwarder for data recording
	backendForwarder, err := forwarder.NewBackendForwarder(cfg.BackendGRPCAddress, 100, sugar)
	if err != nil {
		sugar.Warnf("Failed to create backend forwarder: %v", err)
	} else {
		sugar.Info("Backend forwarder initialized")
	}

	// Initialize WebSocket server for Frontend direct communication
	wsServer := websocket.NewServer(robotManager, sugar, cfg.JWTSecret)
	if backendForwarder != nil {
		wsServer.SetBackendForwarder(backendForwarder)
	}

	// Start WebSocket server hub
	go wsServer.Run()

	// Start WebSocket HTTP server
	go func() {
		wsAddr := ":" + cfg.WebSocketPort
		sugar.Infof("Starting WebSocket server on %s", wsAddr)
		if err := wsServer.Start(wsAddr); err != nil {
			sugar.Fatalf("Failed to start WebSocket server: %v", err)
		}
	}()

	// Initialize gRPC server (for Backend data recording)
	grpcServer := grpcserver.NewServer(robotManager, sugar)

	// Start gRPC server in goroutine
	go func() {
		grpcAddr := ":" + cfg.GRPCPort
		sugar.Infof("Starting Fleet Gateway gRPC server on %s", grpcAddr)
		if err := grpcServer.Start(grpcAddr); err != nil {
			sugar.Fatalf("Failed to start gRPC server: %v", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	sugar.Info("Shutting down server...")

	// Cleanup
	if backendForwarder != nil {
		backendForwarder.Close()
	}
	mqttClient.Disconnect()
	sugar.Info("Server exited")
}
