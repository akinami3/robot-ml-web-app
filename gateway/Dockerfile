FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache git protobuf

# Install protoc-gen-go and protoc-gen-go-grpc
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.32.0 && \
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.3.0

# Copy go mod files
COPY go.mod ./

# Copy source code
COPY . .

# Generate protobuf code from main proto definition
RUN protoc --go_out=. --go_opt=paths=source_relative \
    --go-grpc_out=. --go-grpc_opt=paths=source_relative \
    proto/fleet.proto

# Download dependencies and generate go.sum
RUN go mod tidy

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o /gateway ./cmd/gateway

# Final stage
FROM alpine:3.19

RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

# Copy binary from builder
COPY --from=builder /gateway .

# Create non-root user
RUN adduser -D -g '' appuser
USER appuser

# Expose gRPC and WebSocket ports
EXPOSE 50051 8082

# Run the application
CMD ["./gateway"]
