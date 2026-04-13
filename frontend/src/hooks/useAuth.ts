import { useMutation } from "@tanstack/react-query";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";
import type { LoginRequest, RegisterRequest } from "@/types";
import { notify } from "@/lib/toast";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "@/config/routes";

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const tokenRes = await authService.login(data);
      localStorage.setItem("access_token", tokenRes.access_token);
      const user = await authService.getProfile();
      return { token: tokenRes.access_token, user };
    },
    onSuccess: ({ token, user }) => {
      setAuth(token, user);
      notify.info(`Welcome back, ${user.email.split("@")[0]}!`, "Your dashboard is ready");
      navigate(ROUTES.DASHBOARD);
    },
    onError: (error: Error) => {
      notify.error("Login failed", error.message || "Invalid credentials");
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: RegisterRequest) => authService.register(data),
    onSuccess: () => {
      notify.success("Account created!", "Please log in with your new credentials");
      navigate(ROUTES.LOGIN);
    },
    onError: (error: Error) => {
      notify.error("Registration failed", error.message || "Please try again");
    },
  });
}
