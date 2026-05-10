import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import V2LocationSelect from './V2LocationSelect';

describe('V2LocationSelect', () => {
  it('renders the placeholder when value is empty', () => {
    render(<V2LocationSelect value="" onChange={() => {}} />);
    expect(screen.getByText('Tỉnh/Thành phố')).toBeInTheDocument();
  });

  it('renders the Vietnamese label for the selected enum slug', () => {
    render(<V2LocationSelect value="ha_noi" onChange={() => {}} />);
    expect(screen.getByText('Hà Nội')).toBeInTheDocument();
  });

  it('opens a list of 4 options (3 enums + clear row) on click', async () => {
    render(<V2LocationSelect value="" onChange={() => {}} />);
    await userEvent.click(screen.getByRole('button', { name: /Tỉnh\/Thành phố/i }));
    const options = await screen.findAllByRole('option');
    expect(options).toHaveLength(4);
    expect(screen.getByText('Tất cả khu vực')).toBeInTheDocument();
    expect(screen.getAllByText('Hà Nội').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('TP. Hồ Chí Minh')).toBeInTheDocument();
    expect(screen.getByText('Đà Nẵng')).toBeInTheDocument();
  });

  it('hides the clear row when showClear=false (only 3 options)', async () => {
    render(<V2LocationSelect value="" onChange={() => {}} showClear={false} />);
    await userEvent.click(screen.getByRole('button', { name: /Tỉnh\/Thành phố/i }));
    expect(await screen.findAllByRole('option')).toHaveLength(3);
    expect(screen.queryByText('Tất cả khu vực')).not.toBeInTheDocument();
  });

  it('calls onChange with the enum slug when a location is picked', async () => {
    const onChange = vi.fn();
    render(<V2LocationSelect value="" onChange={onChange} />);
    await userEvent.click(screen.getByRole('button', { name: /Tỉnh\/Thành phố/i }));
    await userEvent.click(screen.getByText('Đà Nẵng'));
    expect(onChange).toHaveBeenCalledWith('da_nang');
  });

  it('calls onChange with empty string when clear row is clicked', async () => {
    const onChange = vi.fn();
    render(<V2LocationSelect value="ha_noi" onChange={onChange} />);
    // Trigger button has fixed aria-label regardless of value.
    await userEvent.click(screen.getByLabelText('Chọn Tỉnh/Thành phố'));
    await userEvent.click(screen.getByText('Tất cả khu vực'));
    expect(onChange).toHaveBeenCalledWith('');
  });

  it('marks the active option with aria-selected', async () => {
    render(<V2LocationSelect value="tp_hcm" onChange={() => {}} />);
    await userEvent.click(screen.getByLabelText('Chọn Tỉnh/Thành phố'));
    const options = await screen.findAllByRole('option');
    const active = options.find((o) => o.getAttribute('aria-selected') === 'true');
    expect(active).toBeDefined();
    expect(active!.textContent).toContain('TP. Hồ Chí Minh');
  });

  it('closes the dropdown on Escape', async () => {
    render(<V2LocationSelect value="" onChange={() => {}} />);
    const trigger = screen.getByRole('button', { name: /Tỉnh\/Thành phố/i });
    await userEvent.click(trigger);
    expect(await screen.findAllByRole('option')).toHaveLength(4);
    await userEvent.keyboard('{Escape}');
    expect(screen.queryAllByRole('option')).toHaveLength(0);
  });

  it('uses a custom placeholder when provided', () => {
    render(
      <V2LocationSelect value="" onChange={() => {}} placeholder="Khu vực làm việc" />
    );
    expect(screen.getByText('Khu vực làm việc')).toBeInTheDocument();
  });
});
