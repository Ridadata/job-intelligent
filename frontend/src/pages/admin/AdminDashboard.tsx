import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity, Users, Database } from "lucide-react";
import { ROUTES } from "@/config/routes";

const items = [
  { icon: <Activity className="h-6 w-6" />, label: "Pipeline Status", description: "Monitor ETL pipeline runs", to: ROUTES.ADMIN_PIPELINE, color: "bg-brand-500/10 text-brand-500" },
  { icon: <Users className="h-6 w-6" />, label: "User Management", description: "Manage user accounts and roles", to: ROUTES.ADMIN_USERS, color: "bg-blue-500/10 text-blue-400" },
  { icon: <Database className="h-6 w-6" />, label: "Data Overview", description: "Source statistics and quality", to: ROUTES.ADMIN, color: "bg-amber-500/10 text-amber-400" },
];

export default function AdminDashboard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">Admin Panel</h1>
        <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
          Platform administration and monitoring
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <Link key={item.to} to={item.to}>
            <div className="group rounded-2xl bg-white dark:bg-[hsl(var(--surface-1))] border border-gray-100 dark:border-white/[0.06] shadow-sm p-6 transition-all duration-300 hover:shadow-md cursor-pointer h-full">
              <div className="flex items-center gap-4">
                <div className={`rounded-xl p-3 ${item.color}`}>
                  {item.icon}
                </div>
                <div>
                  <p className="font-semibold group-hover:text-brand-400 transition-colors">{item.label}</p>
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">{item.description}</p>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </motion.div>
  );
}
