import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ProfilePage from './ProfilePage';
import api from '../lib/api';

const navigateMock = vi.fn();
const loginMock = vi.fn();
const useAuthMock = vi.fn();

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('../components/profile/ProfileHeader', () => ({
  default: ({ user }: any) => <div data-testid="profile-header">{user.name}</div>,
}));

vi.mock('../components/profile/ProfileInfoForm', () => ({
  default: ({ user }: any) => <div data-testid="profile-info">{user.email}</div>,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects to login when user is not authenticated', async () => {
    useAuthMock.mockReturnValue({ isAuthenticated: false, user: null, login: loginMock });

    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/login');
    });
    expect(vi.mocked(api.get)).not.toHaveBeenCalled();
  });

  it('loads profile data from API and renders profile sections', async () => {
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      user: { id: '1', name: 'Fallback', email: 'fb@example.com' },
      login: loginMock,
    });

    vi.mocked(api.get).mockResolvedValue({
      data: { user_id: 1, email: 'alice@example.com', role: 'candidate' },
    } as any);

    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/users/1');
    });

    expect(await screen.findByTestId('profile-header')).toHaveTextContent('alice@example.com');
    expect(screen.getByTestId('profile-info')).toHaveTextContent('alice@example.com');
  });

  it('falls back to auth context user when profile API fails', async () => {
    useAuthMock.mockReturnValue({
      isAuthenticated: true,
      user: { id: '2', name: 'Context User', email: 'context@example.com' },
      login: loginMock,
    });

    vi.mocked(api.get).mockRejectedValue(new Error('network error'));

    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    );

    expect(await screen.findByTestId('profile-header')).toHaveTextContent('Context User');
    expect(screen.getByTestId('profile-info')).toHaveTextContent('context@example.com');
  });
});
