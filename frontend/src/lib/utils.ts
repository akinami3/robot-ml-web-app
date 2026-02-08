import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString();
}

export function formatBattery(battery: number): string {
  return `${Math.round(battery)}%`;
}

export function getStateColor(state: string): string {
  switch (state) {
    case 'IDLE':
      return 'bg-gray-500';
    case 'MOVING':
      return 'bg-green-500';
    case 'PAUSED':
      return 'bg-yellow-500';
    case 'ERROR':
      return 'bg-red-500';
    case 'CHARGING':
      return 'bg-blue-500';
    default:
      return 'bg-gray-400';
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'idle':
      return 'bg-gray-500';
    case 'active':
      return 'bg-green-500';
    case 'charging':
      return 'bg-blue-500';
    case 'error':
      return 'bg-red-500';
    case 'offline':
      return 'bg-gray-400';
    default:
      return 'bg-gray-400';
  }
}

export function getMissionStatusColor(status: string): string {
  switch (status) {
    case 'PENDING':
      return 'bg-gray-500';
    case 'IN_PROGRESS':
      return 'bg-blue-500';
    case 'COMPLETED':
      return 'bg-green-500';
    case 'FAILED':
      return 'bg-red-500';
    case 'CANCELLED':
      return 'bg-yellow-500';
    default:
      return 'bg-gray-400';
  }
}
