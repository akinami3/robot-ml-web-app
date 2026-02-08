'use client';

import { useState } from 'react';
import { useMissions, useCreateMission, useDeleteMission, useRobots } from '@/hooks/useRobots';
import { MissionCard } from '@/components/MissionCard';
import { Plus, X } from 'lucide-react';
import { MissionCreate } from '@/types';

export default function MissionsPage() {
  const { data: missionsData, isLoading } = useMissions();
  const { data: robotsData } = useRobots();
  const missions = missionsData?.missions ?? [];
  const robots = robotsData?.robots ?? [];
  const createMission = useCreateMission();
  const deleteMission = useDeleteMission();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newMission, setNewMission] = useState<MissionCreate>({
    name: '',
    description: '',
    robot_id: 0,
    priority: 1,
    waypoints: [],
  });
  const [waypointInput, setWaypointInput] = useState({ x: '', y: '', action: 'move' });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createMission.mutateAsync(newMission);
      setShowCreateModal(false);
      setNewMission({ name: '', description: '', robot_id: 0, priority: 1, waypoints: [] });
    } catch (error) {
      console.error('Failed to create mission:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this mission?')) {
      try {
        await deleteMission.mutateAsync(id);
      } catch (error) {
        console.error('Failed to delete mission:', error);
      }
    }
  };

  const addWaypoint = () => {
    if (waypointInput.x && waypointInput.y) {
      setNewMission({
        ...newMission,
        waypoints: [
          ...newMission.waypoints,
          {
            x: parseFloat(waypointInput.x),
            y: parseFloat(waypointInput.y),
            action: waypointInput.action,
          },
        ],
      });
      setWaypointInput({ x: '', y: '', action: 'move' });
    }
  };

  const removeWaypoint = (index: number) => {
    setNewMission({
      ...newMission,
      waypoints: newMission.waypoints.filter((_, i) => i !== index),
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Missions</h1>
          <p className="mt-2 text-gray-600">Create and manage robot missions</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 font-medium text-white hover:bg-primary-700"
        >
          <Plus className="h-5 w-5" />
          New Mission
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent"></div>
        </div>
      ) : missions && missions.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {missions.map((mission) => (
            <div key={mission.id} className="relative">
              <MissionCard mission={mission} />
              <button
                onClick={() => handleDelete(mission.id)}
                className="absolute right-2 top-2 rounded-lg bg-red-100 p-2 text-red-600 hover:bg-red-200"
                title="Delete"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl bg-white p-12 text-center">
          <p className="text-gray-500">No missions created yet</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 text-primary-600 hover:underline"
          >
            Create your first mission
          </button>
        </div>
      )}

      {/* Create Mission Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Create New Mission</h2>
              <button onClick={() => setShowCreateModal(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={newMission.name}
                  onChange={(e) => setNewMission({ ...newMission, name: e.target.value })}
                  required
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={newMission.description}
                  onChange={(e) => setNewMission({ ...newMission, description: e.target.value })}
                  rows={3}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Assign Robot</label>
                <select
                  value={newMission.robot_id}
                  onChange={(e) => setNewMission({ ...newMission, robot_id: parseInt(e.target.value) })}
                  required
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
                >
                  <option value={0}>Select a robot</option>
                  {robots?.map((robot) => (
                    <option key={robot.id} value={robot.id}>
                      {robot.name} ({robot.serial_number})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Priority</label>
                <select
                  value={newMission.priority}
                  onChange={(e) => setNewMission({ ...newMission, priority: parseInt(e.target.value) })}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
                >
                  <option value={1}>Low</option>
                  <option value={2}>Medium</option>
                  <option value={3}>High</option>
                </select>
              </div>

              {/* Waypoints */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Waypoints</label>
                <div className="mt-2 space-y-2">
                  {newMission.waypoints.map((wp, index) => (
                    <div key={index} className="flex items-center gap-2 rounded bg-gray-50 p-2">
                      <span className="text-sm">
                        {index + 1}. ({wp.x}, {wp.y}) - {wp.action}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeWaypoint(index)}
                        className="ml-auto text-red-500 hover:text-red-700"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
                <div className="mt-2 flex gap-2">
                  <input
                    type="number"
                    placeholder="X"
                    value={waypointInput.x}
                    onChange={(e) => setWaypointInput({ ...waypointInput, x: e.target.value })}
                    className="w-20 rounded border px-2 py-1"
                  />
                  <input
                    type="number"
                    placeholder="Y"
                    value={waypointInput.y}
                    onChange={(e) => setWaypointInput({ ...waypointInput, y: e.target.value })}
                    className="w-20 rounded border px-2 py-1"
                  />
                  <select
                    value={waypointInput.action}
                    onChange={(e) => setWaypointInput({ ...waypointInput, action: e.target.value })}
                    className="rounded border px-2 py-1"
                  >
                    <option value="move">Move</option>
                    <option value="pickup">Pickup</option>
                    <option value="dropoff">Dropoff</option>
                    <option value="wait">Wait</option>
                  </select>
                  <button
                    type="button"
                    onClick={addWaypoint}
                    className="rounded bg-gray-200 px-3 py-1 hover:bg-gray-300"
                  >
                    Add
                  </button>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border px-4 py-2 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMission.isPending || newMission.robot_id === 0}
                  className="rounded-lg bg-primary-600 px-4 py-2 text-white hover:bg-primary-700 disabled:opacity-50"
                >
                  {createMission.isPending ? 'Creating...' : 'Create Mission'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
