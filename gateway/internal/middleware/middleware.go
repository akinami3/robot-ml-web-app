package middleware

import (
	"net/http"
	"sync"
	"time"

	"go.uber.org/zap"
)

// RateLimiter implements a simple token bucket rate limiter
type RateLimiter struct {
	mu       sync.Mutex
	tokens   map[string]*bucket
	rate     int
	interval time.Duration
	logger   *zap.Logger
}

type bucket struct {
	tokens    int
	lastReset time.Time
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(ratePerMinute int, logger *zap.Logger) *RateLimiter {
	return &RateLimiter{
		tokens:   make(map[string]*bucket),
		rate:     ratePerMinute,
		interval: time.Minute,
		logger:   logger,
	}
}

// Middleware returns an HTTP middleware that applies rate limiting
func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ip := r.RemoteAddr

		if !rl.allow(ip) {
			rl.logger.Warn("Rate limit exceeded", zap.String("ip", ip))
			http.Error(w, "Too Many Requests", http.StatusTooManyRequests)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func (rl *RateLimiter) allow(key string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	b, ok := rl.tokens[key]
	if !ok {
		rl.tokens[key] = &bucket{tokens: rl.rate - 1, lastReset: now}
		return true
	}

	if now.Sub(b.lastReset) >= rl.interval {
		b.tokens = rl.rate - 1
		b.lastReset = now
		return true
	}

	if b.tokens > 0 {
		b.tokens--
		return true
	}

	return false
}

// LoggingMiddleware logs HTTP requests
func LoggingMiddleware(logger *zap.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			next.ServeHTTP(w, r)
			logger.Info("HTTP request",
				zap.String("method", r.Method),
				zap.String("path", r.URL.Path),
				zap.String("remote_addr", r.RemoteAddr),
				zap.Duration("duration", time.Since(start)),
			)
		})
	}
}
