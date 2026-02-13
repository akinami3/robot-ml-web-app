# =============================================================================
# Gateway - Production Dockerfile (Multi-stage)
# =============================================================================
FROM golang:1.22-alpine AS builder

WORKDIR /build

# Install dependencies
RUN apk add --no-cache git ca-certificates

# Copy go.mod and go.sum first for caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o gateway ./cmd/gateway/

# =============================================================================
# Runtime stage - minimal image
# =============================================================================
FROM gcr.io/distroless/static-debian12

WORKDIR /app
COPY --from=builder /build/gateway /app/gateway

USER nonroot:nonroot

EXPOSE 8080 50051

ENTRYPOINT ["/app/gateway"]
