package server

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
	"github.com/robot-ai-webapp/gateway/internal/protocol"
	"go.uber.org/zap"
)

const (
	writeWait      = 10 * time.Second
	pongWait       = 60 * time.Second
	pingPeriod     = (pongWait * 9) / 10
	maxMessageSize = 1024 * 1024 // 1MB
	sendBufferSize = 256
)

// WebSocketServer handles WebSocket connections
type WebSocketServer struct {
	hub      *Hub
	handler  *Handler
	upgrader websocket.Upgrader
	logger   *zap.Logger
	codec    *protocol.Codec
}

// NewWebSocketServer creates a new WebSocket server
func NewWebSocketServer(hub *Hub, handler *Handler, logger *zap.Logger) *WebSocketServer {
	return &WebSocketServer{
		hub:     hub,
		handler: handler,
		logger:  logger,
		codec:   protocol.NewCodec(),
		upgrader: websocket.Upgrader{
			ReadBufferSize:  4096,
			WriteBufferSize: 4096,
			CheckOrigin: func(r *http.Request) bool {
				// In production, validate origin against allowed list
				return true
			},
		},
	}
}

// HandleWebSocket handles a new WebSocket connection
func (s *WebSocketServer) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		s.logger.Error("WebSocket upgrade failed", zap.Error(err))
		return
	}

	clientID := uuid.New().String()
	client := &Client{
		ID:            clientID,
		Conn:          conn,
		Send:          make(chan []byte, sendBufferSize),
		Hub:           s.hub,
		Subscriptions: make(map[string]bool),
		ConnectedAt:   time.Now(),
	}

	s.hub.Register(client)

	// Start read/write pumps
	go s.writePump(client)
	go s.readPump(client)

	s.logger.Info("New WebSocket connection",
		zap.String("client_id", clientID),
		zap.String("remote_addr", r.RemoteAddr),
	)
}

func (s *WebSocketServer) readPump(client *Client) {
	defer func() {
		s.hub.Unregister(client)
		client.Conn.Close()
	}()

	client.Conn.SetReadDeadline(time.Now().Add(pongWait))
	client.Conn.SetPongHandler(func(string) error {
		client.Conn.SetReadDeadline(time.Now().Add(pongWait))
		return nil
	})

	for {
		_, rawMsg, err := client.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				s.logger.Error("WebSocket read error",
					zap.String("client_id", client.ID),
					zap.Error(err),
				)
			}
			return
		}

		// Decode message
		msg, err := s.codec.Decode(rawMsg)
		if err != nil {
			s.logger.Warn("Failed to decode message",
				zap.String("client_id", client.ID),
				zap.Error(err),
			)
			s.sendError(client, "invalid message format")
			continue
		}

		// Handle message
		ctx := context.Background()
		s.handler.HandleMessage(ctx, client, msg)
	}
}

func (s *WebSocketServer) writePump(client *Client) {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		client.Conn.Close()
	}()

	for {
		select {
		case message, ok := <-client.Send:
			client.Conn.SetWriteDeadline(time.Now().Add(writeWait))
			if !ok {
				// Hub closed the channel
				client.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := client.Conn.WriteMessage(websocket.BinaryMessage, message); err != nil {
				s.logger.Error("WebSocket write error",
					zap.String("client_id", client.ID),
					zap.Error(err),
				)
				return
			}

		case <-ticker.C:
			client.Conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := client.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

func (s *WebSocketServer) sendError(client *Client, errMsg string) {
	msg := protocol.NewMessage(protocol.MsgTypeError, "")
	msg.Error = errMsg
	data, err := s.codec.Encode(msg)
	if err != nil {
		return
	}
	select {
	case client.Send <- data:
	default:
	}
}

// ServeHTTP implements http.Handler for the health endpoint
func (s *WebSocketServer) HealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"status":"healthy","clients":%d}`, s.hub.GetClientCount())
}
