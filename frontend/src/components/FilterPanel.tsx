import { useState } from "react";
import { ChevronDown, ChevronUp, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { useFiltersStore } from "@/store/filters.store";

const CONTRACT_TYPES = ["CDI", "CDD", "Freelance", "Internship", "Alternance"];

export function FilterPanel({ className }: { className?: string }) {
  const [open, setOpen] = useState(false);
  const { location, contractType, skills, salaryMin, salaryMax, setFilter, resetFilters } =
    useFiltersStore();
  const [skillInput, setSkillInput] = useState("");

  const activeCount =
    (location ? 1 : 0) +
    (contractType ? 1 : 0) +
    skills.length +
    (salaryMin != null ? 1 : 0) +
    (salaryMax != null ? 1 : 0);

  const addSkill = () => {
    const trimmed = skillInput.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setFilter("skills", [...skills, trimmed]);
    }
    setSkillInput("");
  };

  const removeSkill = (skill: string) => {
    setFilter("skills", skills.filter((s) => s !== skill));
  };

  return (
    <div className={cn("rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4", className)}>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-sm font-medium"
      >
        <span className="flex items-center gap-2">
          Filters
          {activeCount > 0 && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-500/10 text-[10px] font-bold text-brand-400">
              {activeCount}
            </span>
          )}
        </span>
        {open ? <ChevronUp className="h-4 w-4 text-[hsl(var(--muted-foreground))]" /> : <ChevronDown className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />}
      </button>

      {open && (
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 animate-slide-up">
          {/* Location */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[hsl(var(--muted-foreground))]">
              Location
            </label>
            <Input
              value={location}
              onChange={(e) => setFilter("location", e.target.value)}
              placeholder="e.g. Paris"
            />
          </div>

          {/* Contract type */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[hsl(var(--muted-foreground))]">
              Contract type
            </label>
            <select
              value={contractType}
              onChange={(e) => setFilter("contractType", e.target.value)}
              className="flex h-10 w-full rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--surface-1))] px-4 py-2 text-sm transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/30 focus-visible:border-brand-500/50"
            >
              <option value="">All</option>
              {CONTRACT_TYPES.map((ct) => (
                <option key={ct} value={ct}>{ct}</option>
              ))}
            </select>
          </div>

          {/* Salary range */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[hsl(var(--muted-foreground))]">
              Salary range (€)
            </label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={salaryMin ?? ""}
                onChange={(e) => setFilter("salaryMin", e.target.value ? Number(e.target.value) : undefined)}
                placeholder="Min"
              />
              <span className="text-[hsl(var(--muted-foreground))]">–</span>
              <Input
                type="number"
                value={salaryMax ?? ""}
                onChange={(e) => setFilter("salaryMax", e.target.value ? Number(e.target.value) : undefined)}
                placeholder="Max"
              />
            </div>
          </div>

          {/* Skills */}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[hsl(var(--muted-foreground))]">
              Skills
            </label>
            <div className="flex gap-1.5">
              <Input
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                placeholder="Add skill"
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())}
              />
              <Button size="sm" variant="secondary" onClick={addSkill}>Add</Button>
            </div>
            {skills.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {skills.map((s) => (
                  <Badge key={s} variant="secondary" className="cursor-pointer hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/20 transition-colors" onClick={() => removeSkill(s)}>
                    {s} ×
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Reset */}
          {activeCount > 0 && (
            <div className="flex items-end sm:col-span-2 lg:col-span-4">
              <Button variant="ghost" size="sm" onClick={resetFilters} className="gap-1.5">
                <RotateCcw className="h-3.5 w-3.5" />
                Reset filters
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
