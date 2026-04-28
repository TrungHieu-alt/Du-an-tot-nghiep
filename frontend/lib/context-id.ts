export const normalizeContextId = (value: string | null | undefined): string | undefined => {
  if (value == null) return undefined;
  const trimmed = String(value).trim();
  if (!trimmed) return undefined;
  if (trimmed === 'undefined' || trimmed === 'null') return undefined;
  return trimmed;
};

export const isValidContextId = (value: string | null | undefined): value is string =>
  normalizeContextId(value) !== undefined;
