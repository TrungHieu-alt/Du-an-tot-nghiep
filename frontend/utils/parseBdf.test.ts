import { describe, expect, it } from 'vitest';
import { parseBdfApi } from './parseBdf';

describe('parseBdfApi', () => {
  it('throws unsupported message under current backend contract', async () => {
    const file = new File(['pdf-binary'], 'jd.pdf', { type: 'application/pdf' });

    await expect(parseBdfApi(file)).rejects.toThrow(
      'Tính năng parse-bdf chưa được backend hỗ trợ trong contract hiện tại.'
    );
  });
});
