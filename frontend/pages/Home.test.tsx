import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

// Modal & auth contexts: simple stubs so Home renders.
vi.mock('../contexts/ModalContext', () => ({
  useModal: () => ({
    openCvModal: vi.fn(),
    openReqModal: vi.fn(),
  }),
}));
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: false, user: null }),
}));

import Home from './Home';

const renderHome = () =>
  render(
    <MemoryRouter>
      <Home />
    </MemoryRouter>
  );

describe('Home page (V2 search wiring)', () => {
  beforeEach(() => {
    navigateMock.mockReset();
    localStorage.clear();
  });

  it('defaults the search type to "job" and shows the location select', () => {
    renderHome();
    const jobTab = screen.getByRole('tab', { name: /Tìm Job/i });
    expect(jobTab).toHaveAttribute('aria-selected', 'true');
    // Location dropdown is visible only in job mode
    expect(screen.getByLabelText('Chọn Tỉnh/Thành phố')).toBeInTheDocument();
  });

  it('navigates to /v2/search with q + type=job + location when submitting in job mode', async () => {
    renderHome();

    await userEvent.type(screen.getByLabelText('Từ khóa tìm kiếm'), 'backend');
    // Pick a location: open dropdown then click Hà Nội inside the listbox.
    // (Hà Nội also appears in featured-job mock cards on Home; scope to listbox.)
    await userEvent.click(screen.getByLabelText('Chọn Tỉnh/Thành phố'));
    const listbox = await screen.findByRole('listbox');
    await userEvent.click(within(listbox).getByText('Hà Nội'));
    await userEvent.click(screen.getByRole('button', { name: 'Tìm kiếm' }));

    expect(navigateMock).toHaveBeenCalledTimes(1);
    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/v2/search',
      search: 'q=backend&type=job&location=ha_noi',
    });
  });

  it('switches to CV tab, hides location, and emits type=cv on submit', async () => {
    renderHome();

    await userEvent.click(screen.getByRole('tab', { name: /Tìm CV/i }));

    // Location dropdown is gone
    expect(screen.queryByLabelText('Chọn Tỉnh/Thành phố')).not.toBeInTheDocument();

    await userEvent.type(screen.getByLabelText('Từ khóa tìm kiếm'), 'python');
    await userEvent.click(screen.getByRole('button', { name: 'Tìm kiếm' }));

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/v2/search',
      search: 'q=python&type=cv',
    });
  });

  it('drops the location param when CV mode is active even if a location was previously picked', async () => {
    renderHome();

    // Pick a location while in job mode (scope to listbox to disambiguate
    // from "Đà Nẵng" appearing in featured-job mock cards on Home).
    await userEvent.click(screen.getByLabelText('Chọn Tỉnh/Thành phố'));
    const listbox = await screen.findByRole('listbox');
    await userEvent.click(within(listbox).getByText('Đà Nẵng'));

    // Switch to CV
    await userEvent.click(screen.getByRole('tab', { name: /Tìm CV/i }));
    await userEvent.type(screen.getByLabelText('Từ khóa tìm kiếm'), 'react');
    await userEvent.click(screen.getByRole('button', { name: 'Tìm kiếm' }));

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/v2/search',
      search: 'q=react&type=cv',
    });
  });

  it('omits q param when the input is empty/whitespace', async () => {
    renderHome();
    await userEvent.type(screen.getByLabelText('Từ khóa tìm kiếm'), '   ');
    await userEvent.click(screen.getByRole('button', { name: 'Tìm kiếm' }));

    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/v2/search',
      search: 'type=job',
    });
  });

  it('persists searchType in localStorage and restores it on next mount', async () => {
    const { unmount } = renderHome();
    await userEvent.click(screen.getByRole('tab', { name: /Tìm CV/i }));
    expect(localStorage.getItem('v2_search_type')).toBe('cv');
    unmount();

    renderHome();
    const cvTab = screen.getByRole('tab', { name: /Tìm CV/i });
    expect(cvTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.queryByLabelText('Chọn Tỉnh/Thành phố')).not.toBeInTheDocument();
  });

  it('falls back to "job" when localStorage has an unknown value', () => {
    localStorage.setItem('v2_search_type', 'something-weird');
    renderHome();
    const jobTab = screen.getByRole('tab', { name: /Tìm Job/i });
    expect(jobTab).toHaveAttribute('aria-selected', 'true');
  });

  it('submits via Enter key on the search input', async () => {
    renderHome();
    await userEvent.type(
      screen.getByLabelText('Từ khóa tìm kiếm'),
      'devops{Enter}'
    );
    expect(navigateMock).toHaveBeenCalledWith({
      pathname: '/v2/search',
      search: 'q=devops&type=job',
    });
  });
});
