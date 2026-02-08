package api

import (
	"net/http"
	"time"

	"github.com/amr-saas/gateway/internal/config"
	"github.com/amr-saas/gateway/internal/mqtt"
	"github.com/amr-saas/gateway/internal/robot"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.uber.org/zap"
)

// Handler contains API handlers dependencies
type Handler struct {
	config       *config.Config
	robotManager *robot.Manager
	mqttClient   *mqtt.Client
	logger       *zap.SugaredLogger
}

// NewHandler creates a new API handler
func NewHandler(
	cfg *config.Config,
	robotManager *robot.Manager,
	mqttClient *mqtt.Client,
	logger *zap.SugaredLogger,
) *Handler {
	return &Handler{
		config:       cfg,
		robotManager: robotManager,
		mqttClient:   mqttClient,
		logger:       logger,
	}
}

// SetupRouter sets up the Gin router
func SetupRouter(
	cfg *config.Config,
	robotManager *robot.Manager,
	mqttClient *mqtt.Client,
	logger *zap.SugaredLogger,
) *gin.Engine {
	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(LoggerMiddleware(logger))

	handler := NewHandler(cfg, robotManager, mqttClient, logger)

	// Health check
	router.GET("/health", handler.HealthCheck)

	// Metrics
	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// API v1
	v1 := router.Group("/api/v1")
	{
		// Robots
		robots := v1.Group("/robots")
		{
			robots.GET("", handler.ListRobots)
			robots.GET("/:robot_id/status", handler.GetRobotStatus)
		}

		// Commands
		commands := v1.Group("/commands")
		{
			commands.POST("/move", handler.MoveCommand)
			commands.POST("/stop", handler.StopCommand)
		}
	}

	return router
}

// LoggerMiddleware creates a logging middleware
func LoggerMiddleware(logger *zap.SugaredLogger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path

		c.Next()

		latency := time.Since(start)
		status := c.Writer.Status()

		logger.Infow("HTTP request",
			"method", c.Request.Method,
			"path", path,
			"status", status,
			"latency", latency.String(),
			"client_ip", c.ClientIP(),
		)
	}
}

// HealthCheck handles health check requests
func (h *Handler) HealthCheck(c *gin.Context) {
	mqttStatus := "healthy"
	if !h.mqttClient.IsConnected() {
		mqttStatus = "disconnected"
	}

	c.JSON(http.StatusOK, gin.H{
		"status":        "healthy",
		"mqtt":          mqttStatus,
		"robots_online": h.robotManager.GetOnlineRobots(),
		"timestamp":     time.Now().Unix(),
	})
}

// ListRobots returns all registered robots
func (h *Handler) ListRobots(c *gin.Context) {
	robots := h.robotManager.GetAllRobots()
	c.JSON(http.StatusOK, gin.H{
		"total":  len(robots),
		"robots": robots,
	})
}

// GetRobotStatus returns status of a specific robot
func (h *Handler) GetRobotStatus(c *gin.Context) {
	robotID := c.Param("robot_id")

	status, exists := h.robotManager.GetStatus(robotID)
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Robot not found",
		})
		return
	}

	c.JSON(http.StatusOK, status)
}

// MoveCommandRequest represents a move command request
type MoveCommandRequest struct {
	RobotID string `json:"robot_id" binding:"required"`
	Goal    struct {
		X     float64 `json:"x"`
		Y     float64 `json:"y"`
		Theta float64 `json:"theta"`
	} `json:"goal" binding:"required"`
}

// MoveCommand handles move command requests
func (h *Handler) MoveCommand(c *gin.Context) {
	var req MoveCommandRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}

	// Check if robot exists
	robot, exists := h.robotManager.GetRobot(req.RobotID)
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Robot not found",
		})
		return
	}

	if !robot.IsOnline {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Robot is offline",
		})
		return
	}

	// Generate command ID
	commandID := uuid.New().String()

	// Publish command via MQTT
	payload := map[string]interface{}{
		"command_id": commandID,
		"type":       "move",
		"goal": map[string]float64{
			"x":     req.Goal.X,
			"y":     req.Goal.Y,
			"theta": req.Goal.Theta,
		},
		"timestamp": time.Now().Unix(),
	}

	if err := h.mqttClient.PublishCommand(req.RobotID, "move", payload); err != nil {
		h.logger.Errorf("Failed to publish move command: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to send command",
		})
		return
	}

	h.logger.Infof("Move command sent to robot %s: goal=(%.2f, %.2f, %.2f)",
		req.RobotID, req.Goal.X, req.Goal.Y, req.Goal.Theta)

	c.JSON(http.StatusOK, gin.H{
		"success":    true,
		"message":    "Move command sent",
		"command_id": commandID,
	})
}

// StopCommandRequest represents a stop command request
type StopCommandRequest struct {
	RobotID string `json:"robot_id" binding:"required"`
}

// StopCommand handles stop command requests
func (h *Handler) StopCommand(c *gin.Context) {
	var req StopCommandRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}

	// Check if robot exists
	_, exists := h.robotManager.GetRobot(req.RobotID)
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Robot not found",
		})
		return
	}

	// Generate command ID
	commandID := uuid.New().String()

	// Publish command via MQTT
	payload := map[string]interface{}{
		"command_id": commandID,
		"type":       "stop",
		"timestamp":  time.Now().Unix(),
	}

	if err := h.mqttClient.PublishCommand(req.RobotID, "stop", payload); err != nil {
		h.logger.Errorf("Failed to publish stop command: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"message": "Failed to send command",
		})
		return
	}

	h.logger.Infof("Stop command sent to robot %s", req.RobotID)

	c.JSON(http.StatusOK, gin.H{
		"success":    true,
		"message":    "Stop command sent",
		"command_id": commandID,
	})
}
