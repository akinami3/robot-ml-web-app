export interface VelocityCommand {
  robotId: string;
  linear: number;
  angular: number;
}

export interface NavigationGoal {
  robotId: string;
  targetX: number;
  targetY: number;
  orientation: number;
}
