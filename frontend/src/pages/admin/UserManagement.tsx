import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { apiClient } from "@/services/api-client";
import { ENDPOINTS } from "@/config/api";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/EmptyState";
import { Users } from "lucide-react";
import type { UserProfile } from "@/types";

export default function UserManagement() {
  const { data, isLoading, isError } = useQuery<UserProfile[]>({
    queryKey: ["admin", "users"],
    queryFn: () => apiClient.get<UserProfile[]>(ENDPOINTS.ADMIN.USERS),
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/10 text-brand-500">
          <Users className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">User Management</h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            {data?.length ?? 0} registered users
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState title="Failed to load users" />
      ) : data && data.length > 0 ? (
        <div className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[hsl(var(--border))] bg-[hsl(var(--surface-1))]">
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Email</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Role</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">ID</th>
                </tr>
              </thead>
              <tbody>
                {data.map((user) => (
                  <tr key={user.id} className="border-b border-[hsl(var(--border))] last:border-0 hover:bg-[hsl(var(--surface-1))] transition-colors">
                    <td className="px-5 py-3 font-medium">{user.email}</td>
                    <td className="px-5 py-3">
                      <Badge variant={user.role === "admin" ? "default" : "secondary"}>
                        {user.role}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-xs text-[hsl(var(--muted-foreground))] font-mono">
                      {user.id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <EmptyState
          icon={<Users className="h-10 w-10" />}
          title="No users"
          description="Users will appear here once they register"
        />
      )}
    </motion.div>
  );
}
