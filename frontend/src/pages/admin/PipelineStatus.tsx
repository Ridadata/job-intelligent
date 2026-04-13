import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { apiClient } from "@/services/api-client";
import { ENDPOINTS } from "@/config/api";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/EmptyState";
import { Activity, CheckCircle, XCircle, Clock } from "lucide-react";
import type { PipelineRun } from "@/types";

export default function PipelineStatus() {
  const { data, isLoading, isError } = useQuery<PipelineRun[]>({
    queryKey: ["admin", "pipeline-runs"],
    queryFn: () => apiClient.get<PipelineRun[]>(ENDPOINTS.ADMIN.PIPELINE_RUNS),
    refetchInterval: 15_000,
  });

  const statusIcon = (s: PipelineRun["status"]) => {
    switch (s) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-emerald-500" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-amber-500 animate-spin" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/10 text-brand-500">
          <Activity className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Pipeline Status</h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            Real-time ETL monitoring · auto-refreshes every 15 s
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState title="Failed to load pipeline data" />
      ) : data && data.length > 0 ? (
        <div className="space-y-3">
          {data.map((run) => (
            <div key={run.id} className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] overflow-hidden">
              <div className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  {statusIcon(run.status)}
                  <div>
                    <p className="font-medium">{run.stage}</p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">
                      Started {new Date(run.started_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-sm">
                  {run.rows_in != null && (
                    <span className="text-[hsl(var(--muted-foreground))]">In: {run.rows_in}</span>
                  )}
                  {run.rows_out != null && (
                    <span className="text-[hsl(var(--muted-foreground))]">Out: {run.rows_out}</span>
                  )}
                  {run.duration_ms != null && (
                    <span className="text-[hsl(var(--muted-foreground))]">{(run.duration_ms / 1000).toFixed(1)}s</span>
                  )}
                  <Badge
                    variant={
                      run.status === "success"
                        ? "success"
                        : run.status === "failed"
                          ? "destructive"
                          : "secondary"
                    }
                  >
                    {run.status}
                  </Badge>
                </div>
              </div>

              {run.error_message && (
                <div className="border-t border-[hsl(var(--border))] px-4 py-2 text-xs text-red-400 bg-red-500/5">
                  {run.error_message}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Activity className="h-10 w-10" />}
          title="No pipeline runs"
          description="Pipeline runs will appear here once the ETL is triggered"
        />
      )}
    </motion.div>
  );
}
