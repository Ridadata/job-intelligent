import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export function Pagination({ page, totalPages, onPageChange, className }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages: (number | "...")[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push("...");
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
      pages.push(i);
    }
    if (page < totalPages - 2) pages.push("...");
    pages.push(totalPages);
  }

  return (
    <nav className={cn("flex items-center gap-1", className)}>
      <button
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        aria-label="Previous page"
        className="flex h-9 w-9 items-center justify-center rounded-xl border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] transition-all disabled:opacity-40 hover:border-brand-500/30 hover:text-brand-400"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      {pages.map((p, i) =>
        p === "..." ? (
          <span key={`ellipsis-${i}`} className="px-2 text-sm text-[hsl(var(--muted-foreground))]">
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            aria-current={p === page ? "page" : undefined}
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-xl text-sm font-medium transition-all",
              p === page
                ? "bg-brand-500 text-white shadow-glow"
                : "border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] hover:border-brand-500/30 hover:text-brand-400"
            )}
          >
            {p}
          </button>
        )
      )}

      <button
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        aria-label="Next page"
        className="flex h-9 w-9 items-center justify-center rounded-xl border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] transition-all disabled:opacity-40 hover:border-brand-500/30 hover:text-brand-400"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </nav>
  );
}
