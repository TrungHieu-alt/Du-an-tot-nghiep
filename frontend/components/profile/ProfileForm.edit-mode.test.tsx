import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProfileForm from './ProfileForm';

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { id: '1' } }),
}));

describe('ProfileForm strict edit mode', () => {
  it('shows backend-only recruiter fields in edit mode', () => {
    render(
      <ProfileForm
        mode="recruiter"
        isEditMode={true}
        onSubmit={vi.fn()}
        initialData={{ title: 'FE', role: 'Engineer', location: 'HN' } as any}
      />
    );

    expect(screen.getByLabelText('Tiêu đề')).toBeInTheDocument();
    expect(screen.getByLabelText('Vai trò')).toBeInTheDocument();
    expect(screen.getByLabelText('Loại công việc')).toBeInTheDocument();
    expect(screen.queryByText('Thông tin công ty')).not.toBeInTheDocument();
  });

  it('submits strict candidate payload keys in edit mode', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();

    render(
      <ProfileForm
        mode="candidate"
        isEditMode={true}
        onSubmit={onSubmit}
        initialData={{ title: 'CV A', location: 'HCM', skills: ['React'] } as any}
      />
    );

    await user.clear(screen.getByLabelText('Tiêu đề hồ sơ'));
    await user.type(screen.getByLabelText('Tiêu đề hồ sơ'), 'CV Backend');
    await user.click(screen.getByRole('button', { name: 'Lưu thay đổi' }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'CV Backend',
        skills: ['React'],
      })
    );
    expect(onSubmit).toHaveBeenCalledWith(
      expect.not.objectContaining({
        fullname: expect.anything(),
      })
    );
  });
});
