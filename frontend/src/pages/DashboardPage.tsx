import { useQuery } from "@tanstack/react-query";
import { Bot, Database, Activity, MessageSquare } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent, Badge } from "@/components/ui/primitives";
import { robotApi, datasetApi } from "@/services/api";
import { useRobotStore } from "@/stores/robotStore";
import { robotStateColor } from "@/lib/utils";
import type { Robot, Dataset } from "@/types";

export function DashboardPage() {
  const setRobots = useRobotStore((s) => s.setRobots);

  const { data: robots = [] } = useQuery<Robot[]>({
    queryKey: ["robots"],
    queryFn: async () => {
      const res = await robotApi.list();
      setRobots(res.data);
      return res.data;
    },
    refetchInterval: 10000,
  });

  const { data: datasets = [] } = useQuery<Dataset[]>({
    queryKey: ["datasets"],
    queryFn: async () => {
      const res = await datasetApi.list();
      return (res.data as unknown as { items?: Dataset[] }).items ?? res.data;
    },
  });

  const connected = robots.filter((r) => r.state !== "disconnected").length;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard icon={Bot} label="Robots" value={robots.length} sub={`${connected} connected`} />
        <SummaryCard icon={Activity} label="Active" value={connected} sub="online now" />
        <SummaryCard icon={Database} label="Datasets" value={datasets.length} sub="total" />
        <SummaryCard icon={MessageSquare} label="RAG Docs" value="-" sub="uploaded" />
      </div>

      {/* Robot list */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Connected Robots</CardTitle>
        </CardHeader>
        <CardContent>
          {robots.length === 0 ? (
            <p className="text-sm text-muted-foreground">No robots registered.</p>
          ) : (
            <div className="space-y-3">
              {robots.map((r) => (
                <div key={r.id} className="flex items-center justify-between rounded-md border p-3">
                  <div className="flex items-center gap-3">
                    <Bot className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium text-sm">{r.name}</p>
                      <p className="text-xs text-muted-foreground">{r.adapter_type}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground">
                      {r.battery_level != null ? `${r.battery_level.toFixed(0)}%` : "-"}
                    </span>
                    <Badge variant="outline" className={robotStateColor(r.state)}>
                      {r.state}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs text-muted-foreground">
            {label} · {sub}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
