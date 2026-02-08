'use client';

import { useRobots, useMissions } from '@/hooks/useRobots';
import { useAuthStore } from '@/hooks/useAuth';
import { RobotCard } from '@/components/RobotCard';
import { MissionCard } from '@/components/MissionCard';
import { Bot, Target, Activity, AlertTriangle } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { data: robotsData, isLoading: robotsLoading } = useRobots();
  const { data: missionsData, isLoading: missionsLoading } = useMissions();

  const robots = robotsData?.robots ?? [];
  const missions = missionsData?.missions ?? [];

  const stats = {
    totalRobots: robots.length,
    activeRobots: robots.filter((r) => r.status === 'active').length,
    totalMissions: missions.length,
    activeMissions: missions.filter((m) => m.status === 'in_progress' || m.status === 'IN_PROGRESS').length,
    errorRobots: robots.filter((r) => r.status === 'error').length,
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome back, {user?.email}
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl bg-white p-6 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-primary-100 p-3">
              <Bot className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Robots</p>
              <p className="text-2xl font-bold">{stats.totalRobots}</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-green-100 p-3">
              <Activity className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Robots</p>
              <p className="text-2xl font-bold">{stats.activeRobots}</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-blue-100 p-3">
              <Target className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Missions</p>
              <p className="text-2xl font-bold">{stats.activeMissions}</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-red-100 p-3">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Errors</p>
              <p className="text-2xl font-bold">{stats.errorRobots}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Robots */}
      <div>
        <h2 className="mb-4 text-xl font-semibold">Recent Robots</h2>
        {robotsLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent"></div>
          </div>
        ) : robots && robots.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {robots.slice(0, 6).map((robot) => (
              <RobotCard key={robot.id} robot={robot} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-white p-8 text-center text-gray-500">
            No robots registered yet
          </div>
        )}
      </div>

      {/* Recent Missions */}
      <div>
        <h2 className="mb-4 text-xl font-semibold">Recent Missions</h2>
        {missionsLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent"></div>
          </div>
        ) : missions && missions.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {missions.slice(0, 6).map((mission) => (
              <MissionCard key={mission.id} mission={mission} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-white p-8 text-center text-gray-500">
            No missions created yet
          </div>
        )}
      </div>
    </div>
  );
}
