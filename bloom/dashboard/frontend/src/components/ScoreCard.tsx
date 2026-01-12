interface Props {
  label: string;
  score: number | null;
  maxScore?: number;
  description?: string;
}

export function ScoreCard({ label, score, maxScore = 10, description }: Props) {
  const percentage = score !== null ? (score / maxScore) * 100 : 0;
  
  const getScoreColor = (pct: number) => {
    if (pct >= 70) return 'high';
    if (pct >= 40) return 'medium';
    return 'low';
  };

  return (
    <div className="score-card">
      <div className="score-header">
        <span className="score-label">{label}</span>
        <span className={`score-value ${score !== null ? getScoreColor(percentage) : ''}`}>
          {score !== null ? score.toFixed(1) : '--'} / {maxScore}
        </span>
      </div>
      <div className="score-bar">
        <div 
          className={`score-fill ${getScoreColor(percentage)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {description && (
        <div className="score-description">{description}</div>
      )}
    </div>
  );
}

