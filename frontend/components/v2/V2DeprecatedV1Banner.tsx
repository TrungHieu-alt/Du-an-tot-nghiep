import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowRight } from 'lucide-react';
import type { AnchorTypeV2 } from '../../types';

interface V2DeprecatedV1BannerProps {
  /** Which V2 search side to point at when the user clicks the CTA. */
  type: AnchorTypeV2;
  /** Optional className to tweak spacing if the host page already has margin. */
  className?: string;
}

/**
 * Small inline notice for the legacy v1 search pages (/jobs, /candidates) that
 * routes users toward the V2 search experience. The legacy pages still work
 * with their mock dataset, but Home no longer points here — this banner exists
 * so users arriving via Header buttons or stale bookmarks can discover V2.
 */
const V2DeprecatedV1Banner: React.FC<V2DeprecatedV1BannerProps> = ({
  type,
  className = '',
}) => {
  const ctaHref = `/v2/search?type=${type}`;
  const itemLabel = type === 'job' ? 'việc làm' : 'ứng viên';

  return (
    <div
      role="region"
      aria-label="Thông báo trang search cũ"
      className={`bg-amber-50 border-l-4 border-amber-400 rounded-r-xl px-4 py-3 mb-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${className}`}
    >
      <div className="flex items-start sm:items-center gap-3">
        <Sparkles className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5 sm:mt-0" />
        <p className="text-sm text-amber-900">
          Đây là trang tìm {itemLabel} <strong>cũ</strong> với dữ liệu demo.
          {' '}
          <span className="hidden sm:inline">
            Đã có phiên bản tìm kiếm mới với dữ liệu thật + semantic search.
          </span>
        </p>
      </div>
      <Link
        to={ctaHref}
        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-amber-500 text-white font-semibold text-sm hover:bg-amber-600 transition-colors whitespace-nowrap"
      >
        Thử Search V2 <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  );
};

export default V2DeprecatedV1Banner;
