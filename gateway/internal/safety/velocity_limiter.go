package safety

import (
	"math"

	"go.uber.org/zap"
)

// VelocityLimiter clamps velocity commands to configured maximum values
type VelocityLimiter struct {
	maxLinearVel  float64
	maxAngularVel float64
	logger        *zap.Logger
}

// NewVelocityLimiter creates a new velocity limiter
func NewVelocityLimiter(maxLinear, maxAngular float64, logger *zap.Logger) *VelocityLimiter {
	return &VelocityLimiter{
		maxLinearVel:  maxLinear,
		maxAngularVel: maxAngular,
		logger:        logger,
	}
}

// VelocityInput represents a velocity command
type VelocityInput struct {
	LinearX  float64
	LinearY  float64
	AngularZ float64
}

// LimitResult contains the clamped velocity and whether clamping occurred
type LimitResult struct {
	LinearX  float64
	LinearY  float64
	AngularZ float64
	Clamped  bool
}

// Limit clamps velocity values to the configured maximum
func (v *VelocityLimiter) Limit(input VelocityInput) LimitResult {
	result := LimitResult{
		LinearX:  input.LinearX,
		LinearY:  input.LinearY,
		AngularZ: input.AngularZ,
	}

	// Clamp linear velocity
	linearMag := math.Sqrt(input.LinearX*input.LinearX + input.LinearY*input.LinearY)
	if linearMag > v.maxLinearVel {
		scale := v.maxLinearVel / linearMag
		result.LinearX = input.LinearX * scale
		result.LinearY = input.LinearY * scale
		result.Clamped = true
	}

	// Clamp angular velocity
	if math.Abs(input.AngularZ) > v.maxAngularVel {
		if input.AngularZ > 0 {
			result.AngularZ = v.maxAngularVel
		} else {
			result.AngularZ = -v.maxAngularVel
		}
		result.Clamped = true
	}

	if result.Clamped {
		v.logger.Debug("Velocity clamped",
			zap.Float64("req_lx", input.LinearX),
			zap.Float64("req_ly", input.LinearY),
			zap.Float64("req_az", input.AngularZ),
			zap.Float64("out_lx", result.LinearX),
			zap.Float64("out_ly", result.LinearY),
			zap.Float64("out_az", result.AngularZ),
		)
	}

	return result
}
