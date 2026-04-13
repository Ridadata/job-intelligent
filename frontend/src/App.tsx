import { useEffect } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { ROUTES } from "@/config/routes";
import { useAuthStore } from "@/store/auth.store";
import { queryClient } from "@/lib/query-client";
import { AppLayout } from "@/layouts/AppLayout";
import { AuthLayout } from "@/layouts/AuthLayout";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AdminRoute } from "@/components/AdminRoute";
import { ErrorBoundary } from "@/components/ErrorBoundary";

import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import JobSearch from "@/pages/JobSearch";
import JobDetail from "@/pages/JobDetail";
import Recommendations from "@/pages/Recommendations";
import Profile from "@/pages/Profile";
import SavedJobs from "@/pages/SavedJobs";
import SkillGap from "@/pages/SkillGap";
import AdminDashboard from "@/pages/admin/AdminDashboard";
import PipelineStatus from "@/pages/admin/PipelineStatus";
import UserManagement from "@/pages/admin/UserManagement";

function AppRoutes() {
  const hydrate = useAuthStore((s) => s.hydrate);
  useEffect(() => { hydrate(); }, [hydrate]);

  return (
    <Routes>
      {/* Auth routes */}
      <Route element={<AuthLayout />}>
        <Route path={ROUTES.LOGIN} element={<Login />} />
        <Route path={ROUTES.REGISTER} element={<Register />} />
      </Route>

      {/* Protected app routes */}
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
        <Route path={ROUTES.JOBS} element={<JobSearch />} />
        <Route path="/jobs/:id" element={<JobDetail />} />
        <Route path={ROUTES.RECOMMENDATIONS} element={<Recommendations />} />
        <Route path={ROUTES.SKILL_GAP} element={<SkillGap />} />
        <Route path={ROUTES.PROFILE} element={<Profile />} />
        <Route path={ROUTES.SAVED_JOBS} element={<SavedJobs />} />

        {/* Admin routes */}
        <Route path={ROUTES.ADMIN} element={<AdminRoute><AdminDashboard /></AdminRoute>} />
        <Route path={ROUTES.ADMIN_PIPELINE} element={<AdminRoute><PipelineStatus /></AdminRoute>} />
        <Route path={ROUTES.ADMIN_USERS} element={<AdminRoute><UserManagement /></AdminRoute>} />
      </Route>

      {/* Redirect root */}
      <Route path="/" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
      <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <AppRoutes />
        </ErrorBoundary>
      </BrowserRouter>
      <Toaster position="top-right" expand={false} toastOptions={{ unstyled: true }} />
    </QueryClientProvider>
  );
}

export default App;
