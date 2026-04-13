import { toast } from "sonner";
import { CheckCircle, AlertCircle, Info, X } from "lucide-react";
import type { ReactNode } from "react";

interface PremiumToastProps {
  id: string | number;
  icon: ReactNode;
  iconGlow: string;
  title: string;
  description?: string;
  animate?: string;
}

function PremiumToast({ id, icon, iconGlow, title, description, animate }: PremiumToastProps) {
  return (
    <div
      className={`flex items-start gap-3 rounded-xl px-4 py-3 min-w-[320px] max-w-[420px]
        bg-white/70 dark:bg-white/[0.07]
        backdrop-blur-xl border border-slate-200/60 dark:border-white/[0.12]
        shadow-lg shadow-black/5 dark:shadow-black/30
        ${animate ?? ""}`}
    >
      <div
        className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
        style={{ boxShadow: iconGlow }}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 leading-tight">
          {title}
        </p>
        {description && (
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            {description}
          </p>
        )}
      </div>
      <button
        onClick={() => toast.dismiss(id)}
        className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export const notify = {
  success(title: string, description?: string) {
    toast.custom((id) => (
      <PremiumToast
        id={id}
        icon={<CheckCircle className="h-5 w-5 text-emerald-500" />}
        iconGlow="0 0 12px rgba(16,185,129,0.35)"
        title={title}
        description={description}
      />
    ), { duration: 3500 });
  },

  error(title: string, description?: string) {
    toast.custom((id) => (
      <PremiumToast
        id={id}
        icon={<AlertCircle className="h-5 w-5 text-red-500" />}
        iconGlow="0 0 12px rgba(239,68,68,0.35)"
        title={title}
        description={description}
        animate="animate-shake"
      />
    ), { duration: 5000 });
  },

  info(title: string, description?: string) {
    toast.custom((id) => (
      <PremiumToast
        id={id}
        icon={<Info className="h-5 w-5 text-brand-500" />}
        iconGlow="0 0 12px rgba(6,182,212,0.3)"
        title={title}
        description={description}
      />
    ), { duration: 3500 });
  },
};
