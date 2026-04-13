import { useRef } from "react";
import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export function SearchBar({
  value,
  onChange,
  placeholder = "Search jobs...",
  className,
}: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className={cn("relative group", className)}>
      <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[hsl(var(--muted-foreground))] transition-colors group-focus-within:text-brand-500" />
      <input
        ref={inputRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="flex h-12 w-full rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--surface-1))] pl-11 pr-11 text-sm transition-all duration-200 placeholder:text-[hsl(var(--muted-foreground))] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/30 focus-visible:border-brand-500/50"
      />
      {value && (
        <button
          className="absolute right-3 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-lg text-[hsl(var(--muted-foreground))] transition-colors hover:bg-[hsl(var(--surface-2))] hover:text-[hsl(var(--foreground))]"
          onClick={() => {
            onChange("");
            inputRef.current?.focus();
          }}
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}
