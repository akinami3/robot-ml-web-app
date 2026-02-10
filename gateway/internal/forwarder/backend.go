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

// BackendForwarder forwards sensor/control data to backend via gRPC
type BackendForwarder struct {
	backendAddr string
	conn        *grpc.ClientConn
	client      pb.DataRecordingServiceClient
	logger      *zap.SugaredLogger
	buffer      []*pb.SensorDataRecord
	bufferMu    sync.Mutex
	bufferSize  int
	flushTicker *time.Ticker
	stopChan    chan struct{}
}

// NewBackendForwarder creates a new backend forwarder
func NewBackendForwarder(backendAddr string, bufferSize int, logger *zap.SugaredLogger) (*BackendForwarder, error) {
	conn, err := grpc.Dial(backendAddr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		return nil, err
	}

	bf := &BackendForwarder{
		backendAddr: backendAddr,
		conn:        conn,
		client:      pb.NewDataRecordingServiceClient(conn),
		logger:      logger,
		buffer:      make([]*pb.SensorDataRecord, 0, bufferSize),
		bufferSize:  bufferSize,
		flushTicker: time.NewTicker(1 * time.Second),
		stopChan:    make(chan struct{}),
	}

	go bf.flushLoop()

	return bf, nil
}

// ForwardSensorData buffers sensor data for forwarding to backend
func (bf *BackendForwarder) ForwardSensorData(robotID string, sensorData, controlData map[string]float64) error {
	record := &pb.SensorDataRecord{
		RobotId:     robotID,
		Timestamp:   time.Now().UnixMilli(),
		SensorData:  sensorData,
		ControlData: controlData,
	}

	bf.bufferMu.Lock()
	bf.buffer = append(bf.buffer, record)
	shouldFlush := len(bf.buffer) >= bf.bufferSize
	bf.bufferMu.Unlock()

	if shouldFlush {
		go bf.flush()
	}

	return nil
}

// flushLoop periodically flushes the buffer
func (bf *BackendForwarder) flushLoop() {
	for {
		select {
		case <-bf.flushTicker.C:
			bf.flush()
		case <-bf.stopChan:
			bf.flush() // Final flush
			return
		}
	}
}

// flush sends buffered data to backend
func (bf *BackendForwarder) flush() {
	bf.bufferMu.Lock()
	if len(bf.buffer) == 0 {
		bf.bufferMu.Unlock()
		return
	}
	
	records := bf.buffer
	bf.buffer = make([]*pb.SensorDataRecord, 0, bf.bufferSize)
	bf.bufferMu.Unlock()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	req := &pb.BatchSensorDataRequest{
		Records: records,
	}

	resp, err := bf.client.RecordSensorData(ctx, req)
	if err != nil {
		bf.logger.Errorw("Failed to forward sensor data to backend",
			"error", err,
			"record_count", len(records),
		)
		// Re-add to buffer on failure (with limit)
		bf.bufferMu.Lock()
		if len(bf.buffer)+len(records) <= bf.bufferSize*2 {
			bf.buffer = append(records, bf.buffer...)
		} else {
			bf.logger.Warnw("Buffer overflow, dropping old records",
				"dropped", len(records),
			)
		}
		bf.bufferMu.Unlock()
		return
	}

	bf.logger.Debugw("Forwarded sensor data to backend",
		"record_count", resp.RecordedCount,
	)
}

// Close closes the forwarder
func (bf *BackendForwarder) Close() error {
	close(bf.stopChan)
	bf.flushTicker.Stop()
	return bf.conn.Close()
}
