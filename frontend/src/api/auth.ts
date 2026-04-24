
import { http } from './http';
import { apiRoutes } from '../../lib/api-routes';

export interface RegisterDto {
  email: string;
  password: string;
  role?: 'candidate' | 'recruiter';
  name?: string;
}

export interface UserResponse {
  user_id: number;
  email: string;
  role?: 'candidate' | 'recruiter' | 'admin';
  created_at?: string;
  updated_at?: string;
}

export const authApi = {
  register: (dto: RegisterDto) => {
    const payload = {
      email: dto.email,
      password: dto.password,
      role: dto.role,
    };
    return http<UserResponse>(apiRoutes.users.register(), {
      method: 'POST',
      body: payload,
    });
  },
};
