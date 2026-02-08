package robot

// FSM represents a Finite State Machine for robot state management
type FSM struct {
	currentState State
	transitions  map[State][]State
}

// NewFSM creates a new FSM with predefined transitions
func NewFSM(initialState State) *FSM {
	fsm := &FSM{
		currentState: initialState,
		transitions: map[State][]State{
			StateIdle: {StateMoving, StateCharging, StateError},
			StateMoving: {StateIdle, StatePaused, StateError},
			StatePaused: {StateMoving, StateIdle, StateError},
			StateCharging: {StateIdle, StateError},
			StateError: {StateIdle},
		},
	}
	return fsm
}

// CurrentState returns the current state
func (f *FSM) CurrentState() State {
	return f.currentState
}

// CanTransitionTo checks if transition to target state is allowed
func (f *FSM) CanTransitionTo(target State) bool {
	allowedStates, exists := f.transitions[f.currentState]
	if !exists {
		return false
	}

	for _, state := range allowedStates {
		if state == target {
			return true
		}
	}
	return false
}

// TransitionTo transitions to a new state if allowed
func (f *FSM) TransitionTo(target State) bool {
	if !f.CanTransitionTo(target) {
		return false
	}
	f.currentState = target
	return true
}

// ForceState forces a state change (for error recovery)
func (f *FSM) ForceState(state State) {
	f.currentState = state
}
