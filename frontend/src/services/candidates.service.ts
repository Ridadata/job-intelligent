import { apiClient } from "./api-client";
import { ENDPOINTS } from "@/config/api";
import type { CandidateProfile } from "@/types";

export const candidatesService = {
  async getProfile(): Promise<CandidateProfile> {
    return apiClient.get<CandidateProfile>(ENDPOINTS.CANDIDATES.PROFILE);
  },

  async createProfile(data: Partial<CandidateProfile>): Promise<CandidateProfile> {
    return apiClient.post<CandidateProfile>(ENDPOINTS.CANDIDATES.PROFILE, data);
  },

  async updateProfile(data: Partial<CandidateProfile>): Promise<CandidateProfile> {
    return apiClient.put<CandidateProfile>(ENDPOINTS.CANDIDATES.PROFILE, data);
  },

  async uploadCV(file: File): Promise<{ id: string; parsing_status: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("access_token");
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL || "/api/v1"}${ENDPOINTS.CANDIDATES.CV}`,
      { method: "POST", body: formData, headers }
    );
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },
};
