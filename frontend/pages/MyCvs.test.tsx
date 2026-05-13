import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../src/api/normal', () => ({
  createCv: vi.fn(),
  deleteCv: vi.fn(),
  extractCvPdf: vi.fn(),
  listMyCvs: vi.fn(),
  updateCv: vi.fn(),
}));

import MyCvs from './MyCvs';
import { useAuth } from '../contexts/AuthContext';
import { createCv, extractCvPdf, listMyCvs, updateCv } from '../src/api/normal';
import type { NormalCv } from '../types';

const mockedUseAuth = vi.mocked(useAuth);
const mockedListMyCvs = vi.mocked(listMyCvs);
const mockedUpdateCv = vi.mocked(updateCv);
const mockedExtractCvPdf = vi.mocked(extractCvPdf);
const mockedCreateCv = vi.mocked(createCv);

const authValue = {
  accessToken: 'token',
  user: {
    id: 'user-1',
    email: 'nguyen@example.com',
    full_name: 'Nguyen Van A',
    role: 'candidate' as const,
  },
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  googleLogin: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshMe: vi.fn(),
};

const cv = (overrides: Partial<NormalCv> = {}): NormalCv => ({
  id: 'cv-1',
  created_by: 'user-1',
  fullname: 'Nguyen Van A',
  email: 'a@example.com',
  phone: null,
  location: { city: 'Hanoi' },
  headline: 'Frontend Developer',
  summary: 'React developer',
  target_role: 'Frontend Developer',
  employment_type: ['fulltime'],
  availability: null,
  skills: [{ name: 'React' }],
  experiences: [],
  education: [],
  certifications: [],
  status: 'published',
  visibility: 'public',
  tags: [],
  file: {},
  archived: false,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
  ...overrides,
});

const PathProbe = () => {
  const location = useLocation();
  return <span data-testid="path">{location.pathname}</span>;
};

const renderPage = (initialPath = '/cvs') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <MyCvs />
      <PathProbe />
    </MemoryRouter>
  );

describe('MyCvs card grid management', () => {
  beforeEach(() => {
    mockedUseAuth.mockReturnValue(authValue);
    mockedListMyCvs.mockReset();
    mockedUpdateCv.mockReset();
    mockedExtractCvPdf.mockReset();
    mockedCreateCv.mockReset();
    mockedUpdateCv.mockResolvedValue(cv());
    mockedCreateCv.mockResolvedValue(cv());
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  it('renders CVs as cards and keeps the plus card visible', async () => {
    mockedListMyCvs.mockResolvedValue([
      cv(),
      cv({
        id: 'cv-2',
        fullname: 'Tran Thi B',
        headline: 'Accountant',
        target_role: 'Accountant',
        visibility: 'private',
        file: {
          originalname: 'tran-thi-b.pdf',
          size: 2048,
          uploaded_at: '2026-01-03T00:00:00Z',
        },
      }),
    ]);

    renderPage();

    expect(await screen.findByRole('heading', { name: /cv của tôi/i })).toBeInTheDocument();
    expect(mockedListMyCvs).toHaveBeenCalledWith('token');
    expect(screen.getByLabelText('Tạo CV mới')).toBeInTheDocument();
    expect(screen.getByText('Nguyen Van A')).toBeInTheDocument();
    expect(screen.getByText('Tran Thi B')).toBeInTheDocument();
    expect(screen.getByText('tran-thi-b.pdf')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /chỉnh sửa/i })).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: /xóa/i })).toHaveLength(2);
  });

  it('navigates from plus card and existing card without using V2 routes', async () => {
    mockedListMyCvs.mockResolvedValue([cv()]);
    const user = userEvent.setup();

    const firstRender = renderPage();

    await screen.findByText('Nguyen Van A');
    await user.click(screen.getByLabelText('Tạo CV mới'));
    expect(screen.getByTestId('path')).toHaveTextContent('/cvs/new');

    firstRender.unmount();
    renderPage();
    await screen.findByText('Nguyen Van A');
    await user.click(screen.getByRole('link', { name: /mở cv nguyen van a/i }));
    expect(screen.getByTestId('path')).toHaveTextContent('/cvs/cv-1');
  });

  it('keeps action button clicks from navigating the card', async () => {
    mockedListMyCvs.mockResolvedValue([cv()]);
    const user = userEvent.setup();

    renderPage();

    await screen.findByText('Nguyen Van A');
    await user.click(screen.getByRole('button', { name: /ẩn/i }));

    expect(mockedUpdateCv).toHaveBeenCalledWith('token', 'cv-1', {
      status: 'published',
      visibility: 'private',
      archived: false,
    });
    expect(screen.getByTestId('path')).toHaveTextContent('/cvs');
  });

  it('shows an empty state while still rendering the plus card', async () => {
    mockedListMyCvs.mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText(/bạn chưa có cv nào/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Tạo CV mới')).toBeInTheDocument();
  });

  it('extracts a PDF into the create form and saves only after review', async () => {
    mockedListMyCvs.mockResolvedValue([]);
    mockedExtractCvPdf.mockResolvedValue({
      extractedText: 'Nguyen Van A\nEmail: a@example.com',
      cv: {
        fullname: 'Nguyen Van A',
        email: 'a@example.com',
        target_role: 'Frontend Developer',
        employment_type: ['fulltime'],
        skills: [{ name: 'React' }],
      },
      warnings: ['Used deterministic rule-based CV parser; review extracted fields before saving.'],
    });
    const user = userEvent.setup();
    const file = new File(['%PDF-1.4'], 'cv.pdf', { type: 'application/pdf' });

    renderPage('/cvs/upload');

    await user.upload(screen.getByLabelText(/pdf/i, { selector: 'input' }), file);
    await user.click(screen.getByRole('button', { name: /trích xuất cv pdf/i }));

    expect(mockedExtractCvPdf).toHaveBeenCalledWith('token', file);
    expect(screen.getByTestId('path')).toHaveTextContent('/cvs/new');
    expect(await screen.findByDisplayValue('Nguyen Van A')).toBeInTheDocument();
    expect(screen.getByDisplayValue('a@example.com')).toBeInTheDocument();
    expect(screen.getByText(/cảnh báo trích xuất pdf/i)).toBeInTheDocument();
    expect(mockedCreateCv).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: /^tạo cv mới$/i }));
    expect(mockedCreateCv).toHaveBeenCalledWith('token', expect.objectContaining({
      fullname: 'Nguyen Van A',
      email: 'a@example.com',
      target_role: 'Frontend Developer',
    }));
  });
});
