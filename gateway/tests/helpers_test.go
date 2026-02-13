package tests

import (
	"github.com/robot-ai-webapp/gateway/internal/adapter"
	"github.com/robot-ai-webapp/gateway/internal/adapter/mock"
	"go.uber.org/zap"
)

func setupMockRegistry(logger *zap.Logger) *adapter.Registry {
	registry := adapter.NewRegistry(logger)
	registry.RegisterFactory("mock", mock.Factory)
	return registry
}
