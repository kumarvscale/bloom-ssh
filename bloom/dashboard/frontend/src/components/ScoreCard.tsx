interface Props {
  label?: string;
  score?: number | null;
  maxScore?: number;
  description?: string;
  judgment?: any; // Legacy prop for backward compatibility
}

export function ScoreCard({ label, score, maxScore = 10, description, judgment }: Props) {
  // Handle legacy judgment prop
  if (judgment && !label && score === undefined) {
    // Check if it's a harmfulness judgment
    if (judgment.judgment_type === 'assistant_harmfulness') {
      const harmScore = judgment.summary_statistics?.average_harmfulness_score;
      return (
        <div className="score-card harmfulness-legacy">
          <div className="score-header">
            <span className="score-label">🛡️ Harmfulness Score</span>
            <span className={`score-value ${getScoreColorForHarm(harmScore)}`}>
              {harmScore !== null && harmScore !== undefined ? harmScore.toFixed(1) : '--'} / 10
            </span>
          </div>
          <div className="score-bar">
            <div 
              className={`score-fill ${getScoreColorForHarm(harmScore)}`}
              style={{ width: `${(harmScore || 0) * 10}%` }}
            />
          </div>
          <div className="score-description">Higher = more harmful response</div>
        </div>
      );
    } else {
      // Regular judgment
      const behaviorScore = judgment.summary_statistics?.average_behavior_presence_score;
      return (
        <div className="score-card">
          <div className="score-header">
            <span className="score-label">Behavior Presence</span>
            <span className={`score-value ${getScoreColor(behaviorScore)}`}>
              {behaviorScore !== null && behaviorScore !== undefined ? behaviorScore.toFixed(1) : '--'} / 10
            </span>
          </div>
          <div className="score-bar">
            <div 
              className={`score-fill ${getScoreColor(behaviorScore)}`}
              style={{ width: `${(behaviorScore || 0) * 10}%` }}
            />
          </div>
        </div>
      );
    }
  }

  // Normal mode with direct props
  const percentage = score !== null && score !== undefined ? (score / maxScore) * 100 : 0;
  
  return (
    <div className="score-card">
      <div className="score-header">
        <span className="score-label">{label || 'Score'}</span>
        <span className={`score-value ${score !== null && score !== undefined ? getScoreColor(score) : ''}`}>
          {score !== null && score !== undefined ? score.toFixed(1) : '--'} / {maxScore}
        </span>
      </div>
      <div className="score-bar">
        <div 
          className={`score-fill ${getScoreColor(score || 0)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {description && (
        <div className="score-description">{description}</div>
      )}
    </div>
  );
}

function getScoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return '';
  const pct = score * 10;
  if (pct >= 70) return 'high';
  if (pct >= 40) return 'medium';
  return 'low';
}

function getScoreColorForHarm(score: number | null | undefined): string {
  // For harmfulness, higher scores are worse (red)
  if (score === null || score === undefined) return '';
  if (score >= 7) return 'low';  // High harm = red (low color in CSS)
  if (score >= 4) return 'medium';
  return 'high';  // Low harm = green (high color in CSS)
}

