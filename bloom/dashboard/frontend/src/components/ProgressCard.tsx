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
      <div className="card">
        <h3>Run Status</h3>
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
    <div className="card">
      <h3>Run Status</h3>
      
      <div className="status-badge" data-status={status.is_running ? 'running' : 'idle'}>
        {status.is_running ? '● Running' : '○ Idle'}
      </div>

      {/* Overall Progress */}
      <div className="progress-section">
        <div className="progress-header">
          <span>Overall Progress</span>
          <span>{status.progress_pct.toFixed(1)}%</span>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${status.progress_pct}%` }}
          />
        </div>
        <div className="progress-details">
          <span>Test {status.current_test_number} / {status.total_tests}</span>
          <span>ETA: {formatEta(status.eta_seconds)}</span>
        </div>
      </div>

      {/* Current Test Details */}
      {status.is_running && status.current_behavior && (
        <div className="current-status">
          <div className="current-label">Currently evaluating:</div>
          <div className="current-behavior">{status.current_behavior}</div>
          <div className="current-details">
            {status.current_turn_count} turns
          </div>
          
          {/* Pipeline Stage Progress */}
          <div className="stage-progress">
            {status.stages?.map((stage) => (
              <div 
                key={stage.name} 
                className={`stage-item ${stage.status}`}
                title={`${stage.name}: ${formatDuration(stage.avg_duration)}`}
              >
                <span className="stage-icon">{STAGE_ICONS[stage.name] || '•'}</span>
                <span className="stage-name">{stage.name}</span>
                {stage.status === 'running' && <span className="stage-spinner">⏳</span>}
                {stage.status === 'completed' && <span className="stage-check">✓</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Test Configuration */}
      {status.total_behaviors > 0 && (
        <div className="config-info">
          <span className="config-item">
            📋 {status.total_behaviors} behaviors
          </span>
          <span className="config-item">
            🔄 Turns: {status.turn_counts?.join(', ') || '--'}
          </span>
        </div>
      )}

      {status.failed_tests > 0 && (
        <div className="failed-count">
          ⚠️ {status.failed_tests} failed
        </div>
      )}
    </div>
  );
}

