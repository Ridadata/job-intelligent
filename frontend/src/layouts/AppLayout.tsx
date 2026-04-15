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
      className="flex h-8 w-8 items-center justify-center rounded-lg"
      style={{ border: "1px solid var(--border-dim)", background: "var(--btn-subtle-bg)" }}
      aria-label="Toggle theme"
    >
      <Icon className="h-4 w-4" style={{ color: "var(--text-muted)" }} />
    </button>
  );
}

export function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuthStore();

  const allItems = user?.role === "admin" ? [...navItems, ...adminItems] : navItems;

  return (
    <div className="flex min-h-screen flex-col" style={{ background: "var(--bg-void)" }}>
      {/* Ambient glow */}
      <div className="ambient-glow" />

      {/* Top Navbar */}
      <header
        className="sticky top-0 z-50"
        style={{
          height: 60,
          background: "var(--header-bg)",
          backdropFilter: "blur(20px) saturate(180%)",
          WebkitBackdropFilter: "blur(20px) saturate(180%)",
          borderBottom: "1px solid var(--border-dim)",
        }}
      >
        <div className="mx-auto flex h-full max-w-container items-center px-4 lg:px-8">
          {/* Logo — LEFT */}
          <Link to={ROUTES.DASHBOARD} className="flex shrink-0 items-center gap-2.5 group mr-8">
            <div
              className="flex h-8 w-8 items-center justify-center rounded-lg"
              style={{ background: "linear-gradient(135deg, #06B6D4, #0EA5E9)" }}
            >
              <img
                src="/images/web_site_logo.png"
                alt="J"
                className="h-4 w-4 object-contain brightness-0 invert"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                  (e.target as HTMLImageElement).parentElement!.innerHTML =
                    '<span class="text-xs font-extrabold text-white">J</span>';
                }}
              />
            </div>
            <span className="hidden text-base font-bold sm:block" style={{ color: "var(--text-primary)" }}>
              Job Intelligent
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
                  className="flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-sm font-medium transition-all duration-200"
                  style={{
                    color: active ? "var(--text-primary)" : "var(--text-muted)",
                    background: active ? "transparent" : "transparent",
                  }}
                  onMouseEnter={(e) => {
                    if (!active) {
                      e.currentTarget.style.color = "var(--text-primary)";
                      e.currentTarget.style.background = "var(--hover-bg)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!active) {
                      e.currentTarget.style.color = "var(--text-muted)";
                      e.currentTarget.style.background = "transparent";
                    }
                  }}
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
              className="hidden h-8 w-8 items-center justify-center rounded-lg transition-colors hover:bg-red-500/10 sm:flex"
              style={{ border: "1px solid var(--border-dim)", background: "var(--btn-subtle-bg)", color: "var(--text-muted)" }}
              aria-label="Logout"
            >
              <LogOut className="h-4 w-4" />
            </button>

            {/* Mobile menu toggle */}
            <button
              className="flex h-8 w-8 items-center justify-center rounded-lg md:hidden"
              style={{ border: "1px solid var(--border-dim)", background: "var(--btn-subtle-bg)", color: "var(--text-muted)" }}
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
              className="overflow-hidden md:hidden"
              style={{ borderTop: "1px solid var(--border-dim)", background: "var(--mobile-menu-bg)" }}
            >
              <nav className="flex flex-col gap-1 px-4 py-3">
                {allItems.map((item) => {
                  const active = location.pathname === item.path || location.pathname.startsWith(item.path + "/");
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all"
                      style={{
                        color: active ? "var(--text-primary)" : "var(--text-muted)",
                        background: active ? "var(--hover-bg)" : "transparent",
                      }}
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
