import api from '../../lib/api';
import { apiRoutes } from '../../lib/api-routes';

export type UserRole = 'candidate' | 'employer' | 'admin';

export interface AuthUser {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
  role?: Extract<UserRole, 'candidate' | 'employer'>;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  user: AuthUser;
}

export async function register(payload: RegisterPayload): Promise<AuthUser> {
  const response = await api.post<AuthUser>(apiRoutes.auth.register(), payload);
  return response.data;
}

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>(apiRoutes.auth.login(), payload);
  return response.data;
}

export async function getMe(token: string): Promise<AuthUser> {
  const response = await api.get<AuthUser>(apiRoutes.auth.me(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
}

export const authApi = {
  register,
  login,
  getMe,
};
