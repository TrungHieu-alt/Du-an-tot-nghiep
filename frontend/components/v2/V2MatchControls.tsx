import React from 'react';
import { Play, Loader2 } from 'lucide-react';

interface V2MatchControlsProps {
  topK: number;
  minScore: number;
  isRunning: boolean;
  disabled: boolean;
  onTopKChange: (next: number) => void;
  onMinScoreChange: (next: number) => void;
  onRun: () => void;
}

const V2MatchControls: React.FC<V2MatchControlsProps> = ({
  topK,
  minScore,
  isRunning,
  disabled,
  onTopKChange,
  onMinScoreChange,
  onRun,
}) => {
  return (
    <div className="space-y-5">
      {/* top_k */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-semibold text-gray-700">top_k</label>
          <span className="text-sm font-bold text-[#0A65CC] tabular-nums">{topK}</span>
        </div>
        <input
          type="range"
          min={1}
          max={10}
          step={1}
          value={topK}
          onChange={(e) => onTopKChange(Number(e.target.value))}
          className="w-full accent-[#0A65CC]"
        />
        <div className="flex justify-between text-[10px] text-gray-400 mt-1">
          <span>1</span>
          <span>10</span>
        </div>
      </div>

      {/* min_score */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-semibold text-gray-700">min_score</label>
          <span className="text-sm font-bold text-[#00B14F] tabular-nums">{minScore.toFixed(2)}</span>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={minScore}
          onChange={(e) => onMinScoreChange(Number(e.target.value))}
          className="w-full accent-[#00B14F]"
        />
        <div className="flex justify-between text-[10px] text-gray-400 mt-1">
          <span>0.00</span>
          <span>1.00</span>
        </div>
      </div>

      {/* Run button */}
      <button
        type="button"
        onClick={onRun}
        disabled={disabled || isRunning}
        className="w-full px-5 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-[#0A65CC] to-[#00B14F] shadow-md shadow-blue-500/20 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
      >
        {isRunning ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Đang chạy…</span>
          </>
        ) : (
          <>
            <Play className="w-4 h-4" />
            <span>Run Matching V2</span>
          </>
        )}
      </button>
    </div>
  );
};

export default V2MatchControls;
