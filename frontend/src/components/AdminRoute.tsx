import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth.store";
import { ROUTES } from "@/config/routes";

interface AdminRouteProps {
  children: React.ReactNode;
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) return null;

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  if (user?.role !== "admin") {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  return <>{children}</>;
}
