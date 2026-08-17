import apiClient from "./client";

import type {
  RegisterRequest,
  LoginRequest,
  LoginResponse,
  User,
} from "../types/auth";

export const register = async (data: RegisterRequest): Promise<User> => {
  const response = await apiClient.post<User>("/api/auth/register", data);

  return response.data;
};

export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>("/api/auth/login", data);

  return response.data;
};

export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>("/api/auth/me");

  return response.data;
};
