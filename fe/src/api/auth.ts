
import { http } from './http';
import { User } from '../types';

export interface RegisterDto {
  email: string;
  password: string;
  name?: string;
}

export interface AuthResponse {
  accessToken?: string;
  user: User;
}

export const authApi = {
  register: (dto: RegisterDto) => {
    return http<AuthResponse>('/auth/register', {
      method: 'POST',
      body: dto,
    });
  },
};
