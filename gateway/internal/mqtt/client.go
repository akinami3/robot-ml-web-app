package mqtt

import (
	"encoding/json"
	"fmt"
	"time"

	paho "github.com/eclipse/paho.mqtt.golang"
	"github.com/amr-saas/gateway/internal/config"
	"github.com/amr-saas/gateway/internal/robot"
	"go.uber.org/zap"
)

// Client represents an MQTT client
type Client struct {
	client       paho.Client
	config       *config.Config
	robotManager *robot.Manager
	logger       *zap.SugaredLogger
}

// StatusMessage represents robot status message from MQTT
type StatusMessage struct {
	RobotID string  `json:"robot_id"`
	State   string  `json:"state"`
	Battery float64 `json:"battery"`
	Pose    struct {
		X     float64 `json:"x"`
		Y     float64 `json:"y"`
		Theta float64 `json:"theta"`
	} `json:"pose"`
	Timestamp int64 `json:"timestamp"`
}

// NewClient creates a new MQTT client
func NewClient(cfg *config.Config, robotManager *robot.Manager, logger *zap.SugaredLogger) (*Client, error) {
	opts := paho.NewClientOptions()
	opts.AddBroker(fmt.Sprintf("tcp://%s:%d", cfg.MQTTBrokerHost, cfg.MQTTBrokerPort))
	opts.SetClientID(cfg.MQTTClientID)
	opts.SetAutoReconnect(true)
	opts.SetConnectRetry(true)
	opts.SetConnectRetryInterval(5 * time.Second)
	
	// Set Last Will and Testament
	opts.SetWill(
		fmt.Sprintf("%sgateway/status", cfg.MQTTTopicPrefix),
		`{"status": "offline"}`,
		1,
		true,
	)

	client := &Client{
		config:       cfg,
		robotManager: robotManager,
		logger:       logger,
	}

	opts.SetOnConnectHandler(client.onConnect)
	opts.SetConnectionLostHandler(client.onConnectionLost)

	client.client = paho.NewClient(opts)

	return client, nil
}

// Connect connects to the MQTT broker
func (c *Client) Connect() error {
	token := c.client.Connect()
	token.Wait()
	return token.Error()
}

// Disconnect disconnects from the MQTT broker
func (c *Client) Disconnect() {
	// Publish offline status
	c.client.Publish(
		fmt.Sprintf("%sgateway/status", c.config.MQTTTopicPrefix),
		1,
		true,
		`{"status": "offline"}`,
	)
	c.client.Disconnect(250)
}

// IsConnected returns connection status
func (c *Client) IsConnected() bool {
	return c.client.IsConnected()
}

// GetClient returns the underlying MQTT client
func (c *Client) GetClient() paho.Client {
	return c.client
}

// onConnect handles connection events
func (c *Client) onConnect(client paho.Client) {
	c.logger.Info("Connected to MQTT broker")

	// Publish online status
	client.Publish(
		fmt.Sprintf("%sgateway/status", c.config.MQTTTopicPrefix),
		1,
		true,
		`{"status": "online"}`,
	)

	// Subscribe to robot status topics
	statusTopic := fmt.Sprintf("%s+/status", c.config.MQTTTopicPrefix)
	token := client.Subscribe(statusTopic, 1, c.handleStatusMessage)
	token.Wait()
	if token.Error() != nil {
		c.logger.Errorf("Failed to subscribe to %s: %v", statusTopic, token.Error())
	} else {
		c.logger.Infof("Subscribed to %s", statusTopic)
	}

	// Subscribe to robot heartbeat topics
	heartbeatTopic := fmt.Sprintf("%s+/heartbeat", c.config.MQTTTopicPrefix)
	token = client.Subscribe(heartbeatTopic, 0, c.handleHeartbeatMessage)
	token.Wait()
	if token.Error() != nil {
		c.logger.Errorf("Failed to subscribe to %s: %v", heartbeatTopic, token.Error())
	} else {
		c.logger.Infof("Subscribed to %s", heartbeatTopic)
	}
}

// onConnectionLost handles disconnection events
func (c *Client) onConnectionLost(client paho.Client, err error) {
	c.logger.Warnf("Connection to MQTT broker lost: %v", err)
}

// handleStatusMessage handles robot status messages
func (c *Client) handleStatusMessage(client paho.Client, msg paho.Message) {
	var status StatusMessage
	if err := json.Unmarshal(msg.Payload(), &status); err != nil {
		c.logger.Warnf("Failed to parse status message: %v", err)
		return
	}

	c.robotManager.UpdateStatus(
		status.RobotID,
		robot.State(status.State),
		status.Battery,
		robot.Position{
			X:     status.Pose.X,
			Y:     status.Pose.Y,
			Theta: status.Pose.Theta,
		},
	)

	c.logger.Debugf("Received status from %s: state=%s, battery=%.1f",
		status.RobotID, status.State, status.Battery)
}

// handleHeartbeatMessage handles robot heartbeat messages
func (c *Client) handleHeartbeatMessage(client paho.Client, msg paho.Message) {
	var heartbeat struct {
		RobotID string `json:"robot_id"`
		Vendor  string `json:"vendor"`
	}
	if err := json.Unmarshal(msg.Payload(), &heartbeat); err != nil {
		c.logger.Warnf("Failed to parse heartbeat message: %v", err)
		return
	}

	// Register robot if not exists, or update last seen
	c.robotManager.RegisterRobot(heartbeat.RobotID, heartbeat.Vendor, robot.Capabilities{
		SupportsPause:   true,
		SupportsDocking: false,
	})
	c.robotManager.SetOnline(heartbeat.RobotID, true)
}

// PublishCommand publishes a command to robot
func (c *Client) PublishCommand(robotID string, cmdType string, payload interface{}) error {
	topic := fmt.Sprintf("%s%s/command", c.config.MQTTTopicPrefix, robotID)

	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal payload: %w", err)
	}

	token := c.client.Publish(topic, 1, false, jsonPayload)
	token.Wait()
	return token.Error()
}
