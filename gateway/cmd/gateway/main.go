package main

import (
	"os"
	"os/signal"
	"syscall"

	"github.com/amr-saas/gateway/internal/config"
	grpcserver "github.com/amr-saas/gateway/internal/grpc"
	"github.com/amr-saas/gateway/internal/mqtt"
	"github.com/amr-saas/gateway/internal/robot"
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

	// Initialize gRPC server
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
	mqttClient.Disconnect()
	sugar.Info("Server exited")
}
