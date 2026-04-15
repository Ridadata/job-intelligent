import { Outlet } from "react-router-dom";
import { motion } from "framer-motion";

export function AuthLayout() {
  return (
    <div className="flex min-h-screen relative">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-slate-50 via-white to-cyan-50 dark:from-slate-950 dark:via-slate-900 dark:to-cyan-950 items-center justify-center p-12">
        {/* Blurred accent circles */}
        <div className="absolute inset-0 pointer-events-none">
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 8, ease: "easeInOut", repeat: Infinity }}
            className="absolute -top-20 -left-20 h-96 w-96 rounded-full bg-cyan-400 opacity-10 dark:bg-cyan-500 dark:opacity-20 blur-3xl"
          />
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 10, ease: "easeInOut", repeat: Infinity }}
            className="absolute bottom-10 left-16 h-80 w-80 rounded-full bg-blue-400 opacity-10 dark:bg-blue-600 dark:opacity-20 blur-3xl"
          />
        </div>

        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="relative z-10 max-w-md text-center"
        >
          <div className="mx-auto mb-8">
            <img
              src="/images/logo.png"
              alt="radian"
              className="h-14 object-contain dark:brightness-0 dark:invert"
            />
          </div>
          <h1 className="text-4xl font-semibold tracking-tight leading-tight mb-4">
            <span className="text-slate-900 dark:text-white">Match Data Talent</span>
            <br />
            <span className="text-cyan-600 dark:text-cyan-400">with Precision Intelligence</span>
          </h1>
          <p className="text-base text-slate-500 dark:text-slate-400 max-w-sm mx-auto leading-relaxed">
            Your AI co-pilot for data careers
          </p>

          {/* Feature pills */}
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            {["AI Matching", "Smart Recommendations", "Skill Analysis", "Career Insights"].map((feat) => (
              <span
                key={feat}
                className="rounded-full border border-brand-600/25 bg-brand-500/10 px-4 py-1.5 text-sm text-brand-700 dark:border-brand-500/20 dark:bg-brand-500/5 dark:text-brand-300/80 backdrop-blur-sm"
              >
                {feat}
              </span>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Divider — gradient fade line with subtle glow */}
      <div className="hidden lg:block absolute left-1/2 top-0 h-full w-px -translate-x-1/2 z-10 pointer-events-none"
        style={{
          background: "linear-gradient(to bottom, transparent 0%, rgba(6,182,212,0.4) 30%, rgba(6,182,212,0.4) 70%, transparent 100%)",
          boxShadow: "0 0 10px rgba(6,182,212,0.3)",
        }}
      />

      {/* Right panel — form */}
      <div className="flex flex-1 items-center justify-center bg-[hsl(var(--background))] p-6 lg:p-12">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.15, ease: "easeOut" }}
          className="w-full max-w-[440px] space-y-8"
        >
          {/* Mobile-only brand */}
          <div className="text-center lg:hidden">
            <div className="mx-auto mb-4">
              <img
                src="/images/logo.png"
                alt="radian"
                className="h-10 mx-auto object-contain dark:brightness-0 dark:invert"
              />
            </div>
            <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
              AI-powered job matching
            </p>
          </div>
          <Outlet />
        </motion.div>
      </div>
    </div>
  );
}
