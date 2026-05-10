import React from 'react';

interface ScoreBarProps {
  label: string;
  value: number; // 0..1
  accent?: string; // tailwind bg color class
}

const clamp = (v: number) => Math.max(0, Math.min(1, v));

const ScoreBar: React.FC<ScoreBarProps> = ({ label, value, accent = 'bg-[#0A65CC]' }) => {
  const pct = Math.round(clamp(value) * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-600 font-medium">{label}</span>
        <span className="text-gray-900 font-semibold tabular-nums">{pct}%</span>
      </div>
      <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${accent} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
};

interface V2ScoreBarsProps {
  titleScore: number;
  skillsScore: number;
  reqExpScore: number;
  reqSummaryScore: number;
}

const V2ScoreBars: React.FC<V2ScoreBarsProps> = ({
  titleScore,
  skillsScore,
  reqExpScore,
  reqSummaryScore,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <ScoreBar label="Title" value={titleScore} accent="bg-[#0A65CC]" />
      <ScoreBar label="Skills" value={skillsScore} accent="bg-[#00B14F]" />
      <ScoreBar label="Req ↔ Experience" value={reqExpScore} accent="bg-amber-500" />
      <ScoreBar label="Req ↔ Summary" value={reqSummaryScore} accent="bg-purple-500" />
    </div>
  );
};

export default V2ScoreBars;
