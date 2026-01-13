import type { RunStatus } from '../api/client';

interface Props {
  status: RunStatus | null;
}

const STAGE_ICONS: Record<string, string> = {
  understanding: '🔍',
  ideation: '💡',
  rollout: '🎭',
  judgment: '⚖️',
};

export function ProgressCard({ status }: Props) {
  if (!status) {
    return (
      <div className="card progress-card">
        <h3>🚀 Run Status</h3>
        <p className="muted">Loading...</p>
      </div>
    );
  }

  const formatEta = (seconds: number | null) => {
    if (!seconds) return '--';
    if (seconds > 3600) return `${(seconds / 3600).toFixed(1)}h`;
    if (seconds > 60) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds)}s`;
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '--';
    return `~${Math.round(seconds)}s`;
  };

  return (
    <div className="card progress-card">
      <div className="progress-header-row">
        <h3>🚀 Run Status</h3>
        <div className={`status-pill ${status.is_running ? 'running' : 'idle'}`}>
          <span className="status-indicator" />
          {status.is_running ? 'Running' : 'Idle'}
        </div>
      </div>

      {/* Overall Progress */}
      <div className="main-progress">
        <div className="progress-ring-container">
          <svg className="progress-ring" viewBox="0 0 80 80">
            <circle 
              className="progress-ring-bg" 
              cx="40" cy="40" r="34"
              strokeWidth="6"
              fill="none"
            />
            <circle 
              className="progress-ring-fill" 
              cx="40" cy="40" r="34"
              strokeWidth="6"
              fill="none"
              strokeDasharray={`${2 * Math.PI * 34}`}
              strokeDashoffset={`${2 * Math.PI * 34 * (1 - status.progress_pct / 100)}`}
              transform="rotate(-90 40 40)"
            />
          </svg>
          <div className="progress-ring-text">
            <span className="pct">{Math.round(status.progress_pct)}%</span>
          </div>
        </div>
        <div className="progress-info">
          <div className="progress-stat">
            <span className="stat-number">{status.current_test_number}</span>
            <span className="stat-of">of {status.total_tests}</span>
          </div>
          <div className="progress-eta">
            ETA: <strong>{formatEta(status.eta_seconds)}</strong>
          </div>
        </div>
      </div>

      {/* Current Test Details */}
      {status.is_running && status.current_behavior && (
        <div className="current-test">
          <div className="current-test-header">
            <span className="current-label">Evaluating</span>
            <span className="current-turns">{status.current_turn_count} turns</span>
          </div>
          <div className="current-behavior">{status.current_behavior}</div>
          
          {/* Pipeline Stage Progress */}
          <div className="pipeline-stages">
            {status.stages?.map((stage, idx) => (
              <div 
                key={stage.name} 
                className={`pipeline-stage ${stage.status}`}
                title={`${stage.name}: ${formatDuration(stage.avg_duration)}`}
              >
                <span className="stage-icon">{STAGE_ICONS[stage.name]}</span>
                {idx < (status.stages?.length ?? 0) - 1 && (
                  <span className={`stage-connector ${stage.status === 'completed' ? 'completed' : ''}`} />
                )}
              </div>
            ))}
          </div>
          <div className="stage-labels">
            {status.stages?.map((stage) => (
              <span key={stage.name} className={`stage-label ${stage.status}`}>
                {stage.name.slice(0, 3)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="quick-stats">
        <div className="quick-stat">
          <span className="quick-icon">📋</span>
          <span>{status.total_behaviors} behaviors</span>
        </div>
        {status.failed_tests > 0 && (
          <div className="quick-stat error">
            <span className="quick-icon">⚠️</span>
            <span>{status.failed_tests} failed</span>
          </div>
        )}
      </div>
    </div>
  );
}

