interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  onChange: (offset: number) => void;
  className?: string;
}

export default function Pagination({ total, limit, offset, onChange, className = "" }: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const hasPrev = offset > 0;
  const hasNext = offset + limit < total;

  if (total === 0) return null;

  return (
    <div className={`flex items-center justify-between text-sm ${className}`}>
      <span className="text-slate-600">
        Hiển thị <strong>{offset + 1}</strong>–<strong>{Math.min(offset + limit, total)}</strong> trên{" "}
        <strong>{total}</strong> kết quả
      </span>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onChange(Math.max(0, offset - limit))}
          disabled={!hasPrev}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Trang trước"
        >
          ← Trước
        </button>
        <span className="text-slate-600">
          Trang <strong>{currentPage}</strong> / {totalPages}
        </span>
        <button
          type="button"
          onClick={() => onChange(offset + limit)}
          disabled={!hasNext}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Trang sau"
        >
          Sau →
        </button>
      </div>
    </div>
  );
}
