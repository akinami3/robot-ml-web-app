'use client';

import { Mission } from '@/types';
import { cn, formatDate, getMissionStatusColor } from '@/lib/utils';
import { Target, Clock, MapPin } from 'lucide-react';

interface MissionCardProps {
  mission: Mission;
  onCancel?: () => void;
}

export function MissionCard({ mission, onCancel }: MissionCardProps) {
  const canCancel = mission.status === 'PENDING' || mission.status === 'IN_PROGRESS';

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">{mission.name}</h3>
          <p className="text-sm text-gray-500">{mission.mission_id}</p>
        </div>
        <span
          className={cn(
            'inline-flex items-center rounded-full px-2 py-1 text-xs font-medium text-white',
            getMissionStatusColor(mission.status)
          )}
        >
          {mission.status}
        </span>
      </div>

      <div className="mt-4 space-y-2 text-sm text-gray-600">
        {(mission.goal_x !== undefined && mission.goal_y !== undefined) && (
          <div className="flex items-center">
            <Target className="mr-2 h-4 w-4" />
            <span>
              Goal: ({mission.goal_x.toFixed(1)}, {mission.goal_y.toFixed(1)})
            </span>
          </div>
        )}
        {mission.waypoints && mission.waypoints.length > 0 && (
          <div className="flex items-center">
            <MapPin className="mr-2 h-4 w-4" />
            <span>{mission.waypoints.length} waypoints</span>
          </div>
        )}
        <div className="flex items-center">
          <Clock className="mr-2 h-4 w-4" />
          <span>Created: {formatDate(mission.created_at)}</span>
        </div>
        {mission.completed_at && (
          <div className="flex items-center text-green-600">
            <Clock className="mr-2 h-4 w-4" />
            <span>Completed: {formatDate(mission.completed_at)}</span>
          </div>
        )}
      </div>

      {canCancel && onCancel && (
        <div className="mt-4">
          <button
            onClick={onCancel}
            className="w-full rounded bg-red-500 px-4 py-2 text-sm font-medium text-white hover:bg-red-600"
          >
            Cancel Mission
          </button>
        </div>
      )}
    </div>
  );
}
