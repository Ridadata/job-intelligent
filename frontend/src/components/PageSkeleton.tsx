import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

export function PageSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-4", className)}>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="rounded-2xl border border-[hsl(var(--border))] p-5 space-y-3">
          <div className="flex items-start gap-3">
            <Skeleton className="h-10 w-10 rounded-xl" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-5 w-3/4" />
              <div className="flex gap-3">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-20" />
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-6 w-16 rounded-full" />
            <Skeleton className="h-6 w-14 rounded-full" />
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
