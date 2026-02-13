import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle, CardContent, Button, Badge, Input, Select } from "@/components/ui/primitives";
import { datasetApi, recordingApi } from "@/services/api";
import { useRobotStore } from "@/stores/robotStore";
import { formatBytes } from "@/lib/utils";
import { Database, Play, Square, Download, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import type { Dataset, RecordingSession } from "@/types";

export function DataManagementPage() {
  const queryClient = useQueryClient();
  const selectedRobotId = useRobotStore((s) => s.selectedRobotId);
  const robots = useRobotStore((s) => s.robots);

  // Datasets
  const { data: datasets = [] } = useQuery<Dataset[]>({
    queryKey: ["datasets"],
    queryFn: async () => {
      const res = await datasetApi.list();
      return (res.data as unknown as { items?: Dataset[] }).items ?? res.data;
    },
  });

  // Recordings
  const { data: recordings = [] } = useQuery<RecordingSession[]>({
    queryKey: ["recordings"],
    queryFn: async () => {
      const res = await recordingApi.list();
      return (res.data as unknown as { items?: RecordingSession[] }).items ?? res.data;
    },
  });

  // Start recording
  const [recRobotId, setRecRobotId] = useState("");
  const [recName, setRecName] = useState("");
  const startRec = useMutation({
    mutationFn: () =>
      recordingApi.start({
        robot_id: recRobotId || selectedRobotId || "",
        sensor_types: ["lidar", "imu", "odometry"],
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recordings"] });
      toast.success("Recording started");
      setRecName("");
    },
    onError: () => toast.error("Failed to start recording"),
  });

  // Stop recording
  const stopRec = useMutation({
    mutationFn: (id: string) => recordingApi.stop(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recordings"] });
      toast.success("Recording stopped");
    },
  });

  // Delete dataset
  const deleteDs = useMutation({
    mutationFn: (id: string) => datasetApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      toast.success("Dataset deleted");
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Data Management</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recording control */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Play className="h-4 w-4" />
              Recording
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Select value={recRobotId} onChange={(e) => setRecRobotId(e.target.value)} className="flex-1">
                <option value="">Select robot</option>
                {robots.map((r) => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </Select>
              <Input
                placeholder="Session name"
                value={recName}
                onChange={(e) => setRecName(e.target.value)}
                className="flex-1"
              />
            </div>
            <Button
              onClick={() => startRec.mutate()}
              disabled={startRec.isPending || (!recRobotId && !selectedRobotId)}
              className="gap-2"
            >
              <Play className="h-4 w-4" />
              Start Recording
            </Button>

            {/* Active recordings */}
            <div className="space-y-2">
              {recordings
                .filter((r) => r.is_active)
                .map((r) => (
                  <div key={r.id} className="flex items-center justify-between rounded-md border p-2">
                    <div>
                      <p className="text-sm font-medium">Recording {r.id.slice(0, 8)}</p>
                      <p className="text-xs text-muted-foreground">
                        {r.record_count ?? 0} points
                      </p>
                    </div>
                    <Button size="sm" variant="destructive" onClick={() => stopRec.mutate(r.id)} className="gap-1">
                      <Square className="h-3 w-3" />
                      Stop
                    </Button>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* Datasets */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Database className="h-4 w-4" />
              Datasets ({datasets.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {datasets.length === 0 ? (
              <p className="text-sm text-muted-foreground">No datasets yet. Start a recording first.</p>
            ) : (
              <div className="space-y-2">
                {datasets.map((ds) => (
                  <div key={ds.id} className="flex items-center justify-between rounded-md border p-3">
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-sm">{ds.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {ds.record_count ?? 0} records · {formatBytes(ds.size_bytes ?? 0)}
                      </p>
                      <div className="mt-1 flex gap-1">
                        {ds.tags?.map((t) => (
                          <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>
                        ))}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button size="icon" variant="ghost" onClick={() => datasetApi.export(ds.id, "parquet")}>
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button size="icon" variant="ghost" onClick={() => deleteDs.mutate(ds.id)}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Past recordings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recording History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {recordings
              .filter((r) => !r.is_active)
              .map((r) => (
                <div key={r.id} className="flex items-center justify-between rounded-md border p-2 text-sm">
                  <span className="font-medium">Recording {r.id.slice(0, 8)}</span>
                  <div className="flex items-center gap-3 text-muted-foreground">
                    <span>{r.record_count ?? 0} pts</span>
                    <span>{formatBytes(r.size_bytes ?? 0)}</span>
                    <Badge variant={r.stopped_at ? "default" : "destructive"}>
                      {r.stopped_at ? "completed" : "active"}
                    </Badge>
                  </div>
                </div>
              ))}
            {recordings.filter((r) => !r.is_active).length === 0 && (
              <p className="text-sm text-muted-foreground">No past recordings.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
