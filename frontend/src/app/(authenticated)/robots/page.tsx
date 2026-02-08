'use client';

import { useState } from 'react';
import { useRobots, useCreateRobot, useDeleteRobot, useSendCommand } from '@/hooks/useRobots';
import { RobotCard } from '@/components/RobotCard';
import { Plus, X, Send } from 'lucide-react';
import { RobotCreate, Robot } from '@/types';

export default function RobotsPage() {
  const { data: robotsData, isLoading } = useRobots();
  const robots = robotsData?.robots ?? [];
  const createRobot = useCreateRobot();
  const deleteRobot = useDeleteRobot();
  const sendCommand = useSendCommand();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCommandModal, setShowCommandModal] = useState(false);
  const [selectedRobot, setSelectedRobot] = useState<Robot | null>(null);
  const [newRobot, setNewRobot] = useState<RobotCreate>({
    name: '',
    serial_number: '',
    model: '',
    vendor: '',
  });
  const [command, setCommand] = useState('');
  const [commandPayload, setCommandPayload] = useState('{}');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createRobot.mutateAsync(newRobot);
      setShowCreateModal(false);
      setNewRobot({ name: '', serial_number: '', model: '', vendor: '' });
    } catch (error) {
      console.error('Failed to create robot:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this robot?')) {
      try {
        await deleteRobot.mutateAsync(id);
      } catch (error) {
        console.error('Failed to delete robot:', error);
      }
    }
  };

  const handleSendCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRobot) return;
    try {
      const payload = JSON.parse(commandPayload);
      await sendCommand.mutateAsync({
        robotId: selectedRobot.id,
        command,
        payload,
      });
      setShowCommandModal(false);
      setCommand('');
      setCommandPayload('{}');
      setSelectedRobot(null);
    } catch (error) {
      console.error('Failed to send command:', error);
    }
  };

  const openCommandModal = (robot: Robot) => {
    setSelectedRobot(robot);
    setShowCommandModal(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Robots</h1>
          <p className="mt-2 text-gray-600">Manage your fleet of robots</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 font-medium text-white hover:bg-primary-700"
        >
          <Plus className="h-5 w-5" />
          Add Robot
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent"></div>
        </div>
      ) : robots && robots.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {robots.map((robot) => (
            <div key={robot.id} className="relative">
              <RobotCard robot={robot} />
              <div className="absolute right-2 top-2 flex gap-2">
                <button
                  onClick={() => openCommandModal(robot)}
                  className="rounded-lg bg-blue-100 p-2 text-blue-600 hover:bg-blue-200"
                  title="Send Command"
                >
                  <Send className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(robot.id)}
                  className="rounded-lg bg-red-100 p-2 text-red-600 hover:bg-red-200"
                  title="Delete"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl bg-white p-12 text-center">
          <p className="text-gray-500">No robots registered yet</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 text-primary-600 hover:underline"
          >
            Add your first robot
          </button>
        </div>
      )}

      {/* Create Robot Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-xl bg-white p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Add New Robot</h2>
              <button onClick={() => setShowCreateModal(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={newRobot.name}
                  onChange={(e) => setNewRobot({ ...newRobot, name: e.target.value })}
                  required
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Serial Number</label>
                <input
                  type="text"
                  value={newRobot.serial_number}
                  onChange={(e) => setNewRobot({ ...newRobot, serial_number: e.target.value })}
                  required
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Model</label>
                <input
                  type="text"
                  value={newRobot.model}
                  onChange={(e) => setNewRobot({ ...newRobot, model: e.target.value })}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Vendor</label>
                <input
                  type="text"
                  value={newRobot.vendor}
                  onChange={(e) => setNewRobot({ ...newRobot, vendor: e.target.value })}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border px-4 py-2 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createRobot.isPending}
                  className="rounded-lg bg-primary-600 px-4 py-2 text-white hover:bg-primary-700 disabled:opacity-50"
                >
                  {createRobot.isPending ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Send Command Modal */}
      {showCommandModal && selectedRobot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-xl bg-white p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Send Command to {selectedRobot.name}</h2>
              <button onClick={() => setShowCommandModal(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSendCommand} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Command</label>
                <select
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  required
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
                >
                  <option value="">Select a command</option>
                  <option value="start">Start</option>
                  <option value="stop">Stop</option>
                  <option value="pause">Pause</option>
                  <option value="resume">Resume</option>
                  <option value="navigate">Navigate</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Payload (JSON)</label>
                <textarea
                  value={commandPayload}
                  onChange={(e) => setCommandPayload(e.target.value)}
                  rows={4}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-4 py-2 font-mono text-sm focus:border-primary-500 focus:outline-none"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCommandModal(false)}
                  className="rounded-lg border px-4 py-2 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={sendCommand.isPending}
                  className="rounded-lg bg-primary-600 px-4 py-2 text-white hover:bg-primary-700 disabled:opacity-50"
                >
                  {sendCommand.isPending ? 'Sending...' : 'Send'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
