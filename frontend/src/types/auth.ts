export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
