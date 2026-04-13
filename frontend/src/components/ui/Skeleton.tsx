import { cn } from "@/lib/utils";
import { type HTMLAttributes } from "react";

function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-xl shimmer h-4", className)}
      {...props}
    />
  );
}

export { Skeleton };
