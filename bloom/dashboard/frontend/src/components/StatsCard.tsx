import type { Stats } from '../api/client';

interface Props {
  stats: Stats | null;
}

export function StatsCard({ stats }: Props) {
  if (!stats) {
    return (
      <div className="card">
        <h3>Statistics</h3>
        <p className="muted">Loading...</p>
      </div>
    );
  }

  return (
    <div className="card stats-card">
      <h3>Statistics</h3>
      
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-value">{stats.total_behaviors}</div>
          <div className="stat-label">Behaviors</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{stats.completed_tests}</div>
          <div className="stat-label">Completed</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">{stats.failed_tests}</div>
          <div className="stat-label">Failed</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">
            {stats.average_score !== null ? stats.average_score.toFixed(2) : '--'}
          </div>
          <div className="stat-label">Avg Score</div>
        </div>
      </div>

      <div className="behavior-breakdown">
        <div className="breakdown-item completed">
          <span className="dot" />
          <span>{stats.behaviors_completed} Completed</span>
        </div>
        <div className="breakdown-item in-progress">
          <span className="dot" />
          <span>{stats.behaviors_in_progress} In Progress</span>
        </div>
        <div className="breakdown-item pending">
          <span className="dot" />
          <span>{stats.behaviors_pending} Pending</span>
        </div>
      </div>
    </div>
  );
}

