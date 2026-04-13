import { apiClient } from "./api-client";
import { ENDPOINTS } from "@/config/api";
import type { LoginRequest, RegisterRequest, TokenResponse, UserProfile } from "@/types";

export const authService = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>(ENDPOINTS.AUTH.LOGIN, data);
  },

  async register(data: RegisterRequest): Promise<UserProfile> {
    return apiClient.post<UserProfile>(ENDPOINTS.AUTH.REGISTER, data);
  },

  async getProfile(): Promise<UserProfile> {
    return apiClient.get<UserProfile>(ENDPOINTS.AUTH.ME);
  },

  logout() {
    localStorage.removeItem("access_token");
  },
};
