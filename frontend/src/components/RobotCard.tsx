'use client';

import { Robot } from '@/types';
import { cn, formatBattery, getStateColor, getStatusColor } from '@/lib/utils';
import { Battery, MapPin, Wifi, WifiOff } from 'lucide-react';

interface RobotCardProps {
  robot: Robot;
  onClick?: () => void;
}

export function RobotCard({ robot, onClick }: RobotCardProps) {
  const displayState = robot.state || robot.status || 'unknown';
  
  return (
    <div
      onClick={onClick}
      className={cn(
        'cursor-pointer rounded-lg border bg-white p-4 shadow-sm transition-shadow hover:shadow-md',
        robot.is_online ? 'border-gray-200' : 'border-red-200 bg-red-50'
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">{robot.name}</h3>
          <p className="text-sm text-gray-500">{robot.serial_number}</p>
        </div>
        <div className="flex items-center space-x-2">
          {robot.is_online ? (
            <Wifi className="h-4 w-4 text-green-500" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-500" />
          )}
          <span
            className={cn(
              'inline-flex items-center rounded-full px-2 py-1 text-xs font-medium text-white',
              robot.state ? getStateColor(robot.state) : getStatusColor(robot.status)
            )}
          >
            {displayState}
          </span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div className="flex items-center text-gray-600">
          <Battery className="mr-2 h-4 w-4" />
          <span>{formatBattery(robot.battery)}</span>
        </div>
        {(robot.pos_x !== undefined && robot.pos_y !== undefined) && (
          <div className="flex items-center text-gray-600">
            <MapPin className="mr-2 h-4 w-4" />
            <span>
              ({robot.pos_x.toFixed(1)}, {robot.pos_y.toFixed(1)})
            </span>
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
        <span>Vendor: {robot.vendor || 'N/A'}</span>
        {robot.model && <span>Model: {robot.model}</span>}
      </div>
    </div>
  );
}
