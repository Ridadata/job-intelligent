import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  Star,
  Bookmark,
  User,
  Shield,
  Moon,
  Sun,
  Monitor,
  Menu,
  X,
  LogOut,
  Target,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuthStore } from "@/store/auth.store";
import { useThemeStore } from "@/store/theme.store";
import { ROUTES } from "@/config/routes";

const navItems = [
  { label: "Dashboard", icon: LayoutDashboard, path: ROUTES.DASHBOARD },
  { label: "Jobs", icon: Search, path: ROUTES.JOBS },
  { label: "Recommendations", icon: Star, path: ROUTES.RECOMMENDATIONS },
  { label: "Skill Gap", icon: Target, path: ROUTES.SKILL_GAP },
  { label: "Saved Jobs", icon: Bookmark, path: ROUTES.SAVED_JOBS },
  { label: "Profile", icon: User, path: ROUTES.PROFILE },
];

const adminItems = [
  { label: "Admin", icon: Shield, path: ROUTES.ADMIN },
];

function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore();
  const Icon = theme === "dark" ? Moon : theme === "light" ? Sun : Monitor;
  return (
    <button
      onClick={toggleTheme}
      className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 dark:border-white/[0.06] bg-white dark:bg-white/[0.04] text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/[0.06] transition-colors"
      aria-label="Toggle theme"
    >
      <Icon className="h-4 w-4" />
    </button>
  );
}

export function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const allItems = user?.role === "admin" ? [...navItems, ...adminItems] : navItems;

  return (
    <div className="flex min-h-screen flex-col bg-gray-50/50 dark:bg-[hsl(var(--bg-void))]">
      {/* Top Navbar */}
      <header
        className="sticky top-0 z-50 h-[60px] bg-white/80 dark:bg-[hsl(var(--surface-0))]/80 backdrop-blur-xl border-b border-gray-200/60 dark:border-white/[0.06]"
      >
        <div className="mx-auto flex h-full max-w-container items-center px-4 lg:px-8">
          {/* Logo — LEFT */}
          <Link to={ROUTES.DASHBOARD} className="flex shrink-0 items-center gap-2.5 group mr-8">
            <img
              src="/images/logo.png"
              alt="RADIAN"
              className="h-8 w-8 object-contain"
            />
            <span className="hidden text-base font-bold tracking-wide uppercase text-gray-900 dark:text-white sm:block">
              RADIAN
            </span>
          </Link>

          {/* Desktop Nav Links — CENTER */}
          <nav className="hidden flex-1 items-center justify-center gap-1 md:flex">
            {allItems.map((item) => {
              const active = location.pathname === item.path || location.pathname.startsWith(item.path + "/");
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-sm font-medium transition-all duration-200 ${
                    active
                      ? "bg-gray-100 dark:bg-white/[0.06] text-gray-900 dark:text-white"
                      : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/[0.06]"
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right section */}
          <div className="ml-auto flex items-center gap-2.5">
            <ThemeToggle />

            {/* Profile avatar */}
            <Link
              to={ROUTES.PROFILE}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold text-white transition-shadow hover:shadow-glow"
              style={{ background: "linear-gradient(135deg, #06B6D4, #0EA5E9)" }}
            >
              {user?.email?.charAt(0).toUpperCase() ?? "U"}
            </Link>

            {/* Logout */}
            <button
              onClick={logout}
              className="hidden h-8 w-8 items-center justify-center rounded-lg border border-gray-200 dark:border-white/[0.06] bg-white dark:bg-white/[0.04] text-gray-500 dark:text-gray-400 transition-colors hover:bg-red-50 dark:hover:bg-red-500/10 hover:text-red-500 sm:flex"
              aria-label="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>

            {/* Mobile menu toggle */}
            <button
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 dark:border-white/[0.06] bg-white dark:bg-white/[0.04] text-gray-500 dark:text-gray-400 md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden md:hidden border-t border-gray-200 dark:border-white/[0.06] bg-white dark:bg-[hsl(var(--surface-0))]"
            >
              <nav className="flex flex-col gap-1 px-4 py-3">
                {allItems.map((item) => {
                  const active = location.pathname === item.path || location.pathname.startsWith(item.path + "/");
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                        active
                          ? "bg-gray-100 dark:bg-white/[0.06] text-gray-900 dark:text-white"
                          : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-white/[0.06]"
                      }`}
                    >
                      <item.icon className="h-4 w-4" />
                      {item.label}
                    </Link>
                  );
                })}
                <button
                  onClick={() => { logout(); setMobileMenuOpen(false); }}
                  className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-red-400 hover:bg-red-500/10"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </nav>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Page content */}
      <main className="relative flex-1 z-10">
        <div className="relative mx-auto max-w-container px-4 py-8 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
