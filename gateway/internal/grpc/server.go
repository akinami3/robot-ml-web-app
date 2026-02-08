package grpc

import (
	"context"
	"net"
	"time"

	pb "github.com/amr-saas/gateway/proto"
	"github.com/amr-saas/gateway/internal/robot"
	"github.com/google/uuid"
	"go.uber.org/zap"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

const Version = "1.0.0"

// Server implements the FleetGateway gRPC service
type Server struct {
	pb.UnimplementedFleetGatewayServer
	manager   *robot.Manager
	logger    *zap.SugaredLogger
	startTime time.Time
}

// NewServer creates a new gRPC server
func NewServer(manager *robot.Manager, logger *zap.SugaredLogger) *Server {
	return &Server{
		manager:   manager,
		logger:    logger,
		startTime: time.Now(),
	}
}

// Start starts the gRPC server
func (s *Server) Start(addr string) error {
	lis, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}

	grpcServer := grpc.NewServer()
	pb.RegisterFleetGatewayServer(grpcServer, s)

	s.logger.Infow("gRPC server starting", "address", addr)
	return grpcServer.Serve(lis)
}

// StreamRobotStatus streams robot status updates to the client
func (s *Server) StreamRobotStatus(req *pb.StreamRequest, stream pb.FleetGateway_StreamRobotStatusServer) error {
	s.logger.Infow("StreamRobotStatus started", "robot_ids", req.RobotIds, "interval_ms", req.IntervalMs)

	interval := time.Duration(req.IntervalMs) * time.Millisecond
	if interval < 100*time.Millisecond {
		interval = 100 * time.Millisecond
	}

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-stream.Context().Done():
			s.logger.Info("StreamRobotStatus client disconnected")
			return nil
		case <-ticker.C:
			robots := s.manager.GetAllRobots()
			for _, r := range robots {
				// フィルタリング
				if len(req.RobotIds) > 0 {
					found := false
					for _, id := range req.RobotIds {
						if r.ID == id {
							found = true
							break
						}
					}
					if !found {
						continue
					}
				}

				status := robotToProto(r)
				if err := stream.Send(status); err != nil {
					s.logger.Errorw("Failed to send status", "error", err)
					return err
				}
			}
		}
	}
}

// GetAllRobots returns all robot statuses
func (s *Server) GetAllRobots(ctx context.Context, req *pb.Empty) (*pb.RobotList, error) {
	robots := s.manager.GetAllRobots()
	
	pbRobots := make([]*pb.RobotStatus, 0, len(robots))
	for _, r := range robots {
		pbRobots = append(pbRobots, robotToProto(r))
	}

	return &pb.RobotList{
		Robots: pbRobots,
		Total:  int32(len(pbRobots)),
	}, nil
}

// GetRobot returns a specific robot's status
func (s *Server) GetRobot(ctx context.Context, req *pb.RobotId) (*pb.RobotStatus, error) {
	r, err := s.manager.GetRobot(req.Id)
	if err != nil {
		return nil, status.Errorf(codes.NotFound, "robot not found: %s", req.Id)
	}

	return robotToProto(r), nil
}

// SendCommand sends a command to a robot
func (s *Server) SendCommand(ctx context.Context, req *pb.Command) (*pb.CommandResponse, error) {
	s.logger.Infow("SendCommand received",
		"robot_id", req.RobotId,
		"command_type", req.Type.String(),
		"parameters", req.Parameters,
	)

	commandID := uuid.New().String()

	// コマンドタイプに応じた処理
	var err error
	switch req.Type {
	case pb.CommandType_CMD_MOVE:
		x, y := 0.0, 0.0
		if xStr, ok := req.Parameters["x"]; ok {
			// パース処理（簡略化）
			_ = xStr
		}
		if yStr, ok := req.Parameters["y"]; ok {
			_ = yStr
		}
		err = s.manager.MoveRobot(req.RobotId, x, y)
	case pb.CommandType_CMD_STOP:
		err = s.manager.StopRobot(req.RobotId)
	case pb.CommandType_CMD_PAUSE:
		err = s.manager.PauseRobot(req.RobotId)
	case pb.CommandType_CMD_RESUME:
		err = s.manager.ResumeRobot(req.RobotId)
	default:
		return &pb.CommandResponse{
			Success:   false,
			Message:   "unknown command type",
			CommandId: commandID,
		}, nil
	}

	if err != nil {
		return &pb.CommandResponse{
			Success:   false,
			Message:   err.Error(),
			CommandId: commandID,
		}, nil
	}

	return &pb.CommandResponse{
		Success:   true,
		Message:   "command sent successfully",
		CommandId: commandID,
	}, nil
}

// StartMission starts a mission for a robot
func (s *Server) StartMission(ctx context.Context, req *pb.MissionRequest) (*pb.MissionResponse, error) {
	s.logger.Infow("StartMission received",
		"mission_id", req.MissionId,
		"robot_id", req.RobotId,
		"mission_type", req.Type.String(),
		"waypoints_count", len(req.Waypoints),
	)

	// ミッション開始ロジック（簡略化）
	// 実際にはwaypointsを処理してロボットに送信

	return &pb.MissionResponse{
		Success: true,
		Message: "mission started",
		Status:  pb.MissionStatus_MISSION_IN_PROGRESS,
	}, nil
}

// CancelMission cancels a mission
func (s *Server) CancelMission(ctx context.Context, req *pb.MissionId) (*pb.MissionResponse, error) {
	s.logger.Infow("CancelMission received", "mission_id", req.Id)

	// ミッションキャンセルロジック（簡略化）

	return &pb.MissionResponse{
		Success: true,
		Message: "mission cancelled",
		Status:  pb.MissionStatus_MISSION_CANCELLED,
	}, nil
}

// HealthCheck returns the health status of the gateway
func (s *Server) HealthCheck(ctx context.Context, req *pb.Empty) (*pb.HealthResponse, error) {
	robots := s.manager.GetAllRobots()
	uptime := time.Since(s.startTime)

	return &pb.HealthResponse{
		Healthy:         true,
		Version:         Version,
		ConnectedRobots: int32(len(robots)),
		UptimeSeconds:   int64(uptime.Seconds()),
	}, nil
}

// robotToProto converts internal robot model to protobuf
func robotToProto(r *robot.Robot) *pb.RobotStatus {
	state := pb.RobotState_UNKNOWN
	switch r.State {
	case "IDLE":
		state = pb.RobotState_IDLE
	case "MOVING":
		state = pb.RobotState_MOVING
	case "PAUSED":
		state = pb.RobotState_PAUSED
	case "ERROR":
		state = pb.RobotState_ERROR
	case "CHARGING":
		state = pb.RobotState_CHARGING
	case "OFFLINE":
		state = pb.RobotState_OFFLINE
	}

	return &pb.RobotStatus{
		Id:               r.ID,
		Name:             r.Name,
		Vendor:           r.Vendor,
		Model:            r.Model,
		State:            state,
		Position:         &pb.Position{X: r.X, Y: r.Y, Theta: r.Theta},
		BatteryLevel:     int32(r.Battery),
		CurrentMissionId: r.CurrentMissionID,
		LastSeen:         r.LastSeen.UnixMilli(),
		Metadata:         r.Metadata,
	}
}
