package forwarder

import (
"context"
"sync"
"time"

pb "github.com/amr-saas/gateway/proto"
"go.uber.org/zap"
"google.golang.org/grpc"
"google.golang.org/grpc/credentials/insecure"
)

// ============================================================
// Generic Buffer  — DRY pattern for sensor & command buffers
// ============================================================

// flushFunc is called with a batch of records to send via gRPC.
type flushFunc[T any] func(ctx context.Context, records []T) (int32, error)

// recordBuffer is a generic, thread-safe buffer with overflow protection.
type recordBuffer[T any] struct {
mu       sync.Mutex
items    []T
cap      int
flushFn  flushFunc[T]
logger   *zap.SugaredLogger
label    string // for log messages (e.g., "sensor", "command")
}

func newRecordBuffer[T any](capacity int, label string, logger *zap.SugaredLogger, fn flushFunc[T]) *recordBuffer[T] {
return &recordBuffer[T]{
items:   make([]T, 0, capacity),
cap:     capacity,
flushFn: fn,
logger:  logger,
label:   label,
}
}

// add appends a record and returns true if the buffer is full.
func (b *recordBuffer[T]) add(record T) bool {
b.mu.Lock()
defer b.mu.Unlock()
b.items = append(b.items, record)
return len(b.items) >= b.cap
}

// flush drains the buffer and sends records via gRPC.
func (b *recordBuffer[T]) flush() {
b.mu.Lock()
if len(b.items) == 0 {
b.mu.Unlock()
return
}
records := b.items
b.items = make([]T, 0, b.cap)
b.mu.Unlock()

ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

count, err := b.flushFn(ctx, records)
if err != nil {
b.logger.Errorw("Failed to forward "+b.label+" data to backend",
"error", err,
"record_count", len(records),
)
// Re-add on failure (with overflow limit)
b.mu.Lock()
if len(b.items)+len(records) <= b.cap*2 {
b.items = append(records, b.items...)
} else {
b.logger.Warnw(b.label+" buffer overflow, dropping old records",
"dropped", len(records),
)
}
b.mu.Unlock()
return
}

b.logger.Debugw("Forwarded "+b.label+" data to backend",
"record_count", count,
)
}

// ============================================================
// BackendForwarder — orchestrates sensor & command forwarding
// ============================================================

// BackendForwarder forwards sensor/control data and command data
// to the Backend via gRPC DataRecordingService.
type BackendForwarder struct {
conn        *grpc.ClientConn
client      pb.DataRecordingServiceClient
logger      *zap.SugaredLogger

sensorBuf  *recordBuffer[*pb.SensorDataRecord]
commandBuf *recordBuffer[*pb.CommandDataRecord]

flushTicker *time.Ticker
stopChan    chan struct{}
}

// NewBackendForwarder creates a new backend forwarder.
func NewBackendForwarder(backendAddr string, bufferSize int, logger *zap.SugaredLogger) (*BackendForwarder, error) {
conn, err := grpc.Dial(backendAddr,
grpc.WithTransportCredentials(insecure.NewCredentials()),
)
if err != nil {
return nil, err
}

client := pb.NewDataRecordingServiceClient(conn)

bf := &BackendForwarder{
conn:        conn,
client:      client,
logger:      logger,
flushTicker: time.NewTicker(1 * time.Second),
stopChan:    make(chan struct{}),
}

// Initialize typed buffers with their respective gRPC flush functions
bf.sensorBuf = newRecordBuffer(bufferSize, "sensor", logger,
func(ctx context.Context, records []*pb.SensorDataRecord) (int32, error) {
resp, err := client.RecordSensorData(ctx, &pb.BatchSensorDataRequest{Records: records})
if err != nil {
return 0, err
}
return resp.RecordedCount, nil
},
)

bf.commandBuf = newRecordBuffer(bufferSize, "command", logger,
func(ctx context.Context, records []*pb.CommandDataRecord) (int32, error) {
resp, err := client.RecordCommandData(ctx, &pb.BatchCommandDataRequest{Records: records})
if err != nil {
return 0, err
}
return resp.RecordedCount, nil
},
)

go bf.flushLoop()

return bf, nil
}

// ForwardSensorData buffers sensor data for forwarding to backend.
func (bf *BackendForwarder) ForwardSensorData(robotID string, sensorData, controlData map[string]float64) error {
record := &pb.SensorDataRecord{
RobotId:     robotID,
Timestamp:   time.Now().UnixMilli(),
SensorData:  sensorData,
ControlData: controlData,
}
if bf.sensorBuf.add(record) {
go bf.sensorBuf.flush()
}
return nil
}

// ForwardCommandData buffers command data for forwarding to backend.
func (bf *BackendForwarder) ForwardCommandData(
robotID, userID, command string,
params map[string]float64,
success bool,
errorMsg string,
robotStateBefore map[string]float64,
) error {
record := &pb.CommandDataRecord{
RobotId:          robotID,
Timestamp:        time.Now().UnixMilli(),
Command:          command,
Parameters:       params,
UserId:           userID,
Success:          success,
ErrorMessage:     errorMsg,
RobotStateBefore: robotStateBefore,
}
if bf.commandBuf.add(record) {
go bf.commandBuf.flush()
}
return nil
}

// flushLoop periodically flushes both buffers.
func (bf *BackendForwarder) flushLoop() {
for {
select {
case <-bf.flushTicker.C:
bf.sensorBuf.flush()
bf.commandBuf.flush()
case <-bf.stopChan:
bf.sensorBuf.flush()
bf.commandBuf.flush()
return
}
}
}

// Close gracefully shuts down the forwarder, flushing remaining data.
func (bf *BackendForwarder) Close() error {
close(bf.stopChan)
bf.flushTicker.Stop()
return bf.conn.Close()
}
