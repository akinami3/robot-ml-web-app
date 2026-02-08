'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Position, MissionCreate, RobotCreate } from '@/types';

export function useRobots(params?: { skip?: number; limit?: number; vendor?: string; state?: string }) {
  return useQuery({
    queryKey: ['robots', params],
    queryFn: () => api.getRobots(params),
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
  });
}

export function useCreateRobot() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (robot: RobotCreate) => api.createRobot(robot),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['robots'] });
    },
  });
}

export function useDeleteRobot() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (robotId: number) => api.deleteRobot(robotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['robots'] });
    },
  });
}

export function useSendCommand() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ robotId, command, payload }: { robotId: number; command: string; payload: Record<string, unknown> }) =>
      api.sendCommand(robotId, command, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['robots'] });
    },
  });
}

export function useDeleteMission() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (missionId: number) => api.deleteMission(missionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions'] });
    },
  });
}

export function useRobot(robotId: string) {
  return useQuery({
    queryKey: ['robot', robotId],
    queryFn: () => api.getRobot(robotId),
    enabled: !!robotId,
    refetchInterval: 2000,
  });
}

export function useMoveRobot() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ robotId, goal }: { robotId: string; goal: Position }) =>
      api.moveRobot(robotId, goal),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['robots'] });
    },
  });
}

export function useStopRobot() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (robotId: string) => api.stopRobot(robotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['robots'] });
    },
  });
}

export function useMissions(params?: { skip?: number; limit?: number; status?: string; robot_id?: string }) {
  return useQuery({
    queryKey: ['missions', params],
    queryFn: () => api.getMissions(params),
    refetchInterval: 5000,
  });
}

export function useCreateMission() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (mission: MissionCreate) => api.createMission(mission),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions'] });
      queryClient.invalidateQueries({ queryKey: ['robots'] });
    },
  });
}

export function useCancelMission() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (missionId: string) => api.cancelMission(missionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['missions'] });
    },
  });
}
