package server

import (
	"sync"
	"time"

	"github.com/robot-ai-webapp/gateway/internal/protocol"
	"go.uber.org/zap"
)

// Client represents a connected WebSocket client
type Client struct {
	ID            string
	UserID        string
	Conn          WSConn
	Send          chan []byte
	Hub           *Hub
	Authenticated bool
	Subscriptions map[string]bool // robot_id -> subscribed
	mu            sync.RWMutex
	ConnectedAt   time.Time
}

// WSConn is an interface for WebSocket connections (for testability)
type WSConn interface {
	WriteMessage(messageType int, data []byte) error
	ReadMessage() (messageType int, p []byte, err error)
	Close() error
	SetReadDeadline(t time.Time) error
	SetWriteDeadline(t time.Time) error
	SetPongHandler(h func(appData string) error)
}

// Hub manages all WebSocket clients and message routing
type Hub struct {
	clients    map[string]*Client // client_id -> client
	mu         sync.RWMutex
	register   chan *Client
	unregister chan *Client
	broadcast  chan *BroadcastMessage
	logger     *zap.Logger
	codec      *protocol.Codec
}

// BroadcastMessage targets specific robots or all clients
type BroadcastMessage struct {
	RobotID string // empty = broadcast to all
	Data    []byte
}

// NewHub creates a new Hub
func NewHub(logger *zap.Logger) *Hub {
	return &Hub{
		clients:    make(map[string]*Client),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan *BroadcastMessage, 256),
		logger:     logger,
		codec:      protocol.NewCodec(),
	}
}

// Run starts the hub's main loop
func (h *Hub) Run() {
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client.ID] = client
			h.mu.Unlock()
			h.logger.Info("Client registered",
				zap.String("client_id", client.ID),
				zap.String("user_id", client.UserID),
			)

		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client.ID]; ok {
				delete(h.clients, client.ID)
				close(client.Send)
			}
			h.mu.Unlock()
			h.logger.Info("Client unregistered",
				zap.String("client_id", client.ID),
			)

		case msg := <-h.broadcast:
			h.mu.RLock()
			for _, client := range h.clients {
				if !client.Authenticated {
					continue
				}
				// If robot-specific, only send to subscribed clients
				if msg.RobotID != "" {
					client.mu.RLock()
					subscribed := client.Subscriptions[msg.RobotID]
					client.mu.RUnlock()
					if !subscribed {
						continue
					}
				}
				select {
				case client.Send <- msg.Data:
				default:
					// Client send buffer full, skip
					h.logger.Warn("Client send buffer full, dropping message",
						zap.String("client_id", client.ID),
					)
				}
			}
			h.mu.RUnlock()
		}
	}
}

// Register registers a client
func (h *Hub) Register(client *Client) {
	h.register <- client
}

// Unregister unregisters a client
func (h *Hub) Unregister(client *Client) {
	h.unregister <- client
}

// BroadcastToRobot sends data to all clients subscribed to a robot
func (h *Hub) BroadcastToRobot(robotID string, data []byte) {
	h.broadcast <- &BroadcastMessage{
		RobotID: robotID,
		Data:    data,
	}
}

// BroadcastToAll sends data to all authenticated clients
func (h *Hub) BroadcastToAll(data []byte) {
	h.broadcast <- &BroadcastMessage{
		Data: data,
	}
}

// SendToClient sends data to a specific client
func (h *Hub) SendToClient(clientID string, data []byte) {
	h.mu.RLock()
	client, ok := h.clients[clientID]
	h.mu.RUnlock()

	if ok {
		select {
		case client.Send <- data:
		default:
			h.logger.Warn("Client send buffer full",
				zap.String("client_id", clientID),
			)
		}
	}
}

// GetClientCount returns the number of connected clients
func (h *Hub) GetClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}

// SubscribeClient subscribes a client to a robot's sensor data
func (h *Hub) SubscribeClient(clientID, robotID string) {
	h.mu.RLock()
	client, ok := h.clients[clientID]
	h.mu.RUnlock()

	if ok {
		client.mu.Lock()
		client.Subscriptions[robotID] = true
		client.mu.Unlock()
	}
}
