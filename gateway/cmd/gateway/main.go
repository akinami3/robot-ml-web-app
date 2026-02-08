package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/amr-saas/gateway/internal/api"
	"github.com/amr-saas/gateway/internal/config"
	"github.com/amr-saas/gateway/internal/mqtt"
	"github.com/amr-saas/gateway/internal/robot"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func main() {
	// Initialize logger
	logger, _ := zap.NewProduction()
	defer logger.Sync()
	sugar := logger.Sugar()

	// Load configuration
	cfg := config.Load()

	// Set Gin mode
	if cfg.Debug {
		gin.SetMode(gin.DebugMode)
	} else {
		gin.SetMode(gin.ReleaseMode)
	}

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

	// Initialize HTTP server
	router := api.SetupRouter(cfg, robotManager, mqttClient, sugar)

	srv := &http.Server{
		Addr:    ":" + cfg.HTTPPort,
		Handler: router,
	}

	// Start server
	go func() {
		sugar.Infof("Starting Fleet Gateway on port %s", cfg.HTTPPort)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			sugar.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	sugar.Info("Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		sugar.Fatalf("Server forced to shutdown: %v", err)
	}

	mqttClient.Disconnect()
	sugar.Info("Server exited")
}
