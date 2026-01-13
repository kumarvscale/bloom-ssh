import type { Stats } from '../api/client';

interface Props {
  stats: Stats | null;
}

export function StatsCard({ stats }: Props) {
  if (!stats) {
    return (
      <div className="card stats-card">
        <h3>📊 Statistics</h3>
        <p className="muted">Loading...</p>
      </div>
    );
  }

  const js = stats.judgment_stats;
  const hasJudgments = js && js.count > 0;

  // Calculate percentages for visual bars
  const getBarWidth = (value: number, total: number) => 
    total > 0 ? `${(value / total) * 100}%` : '0%';

  return (
    <div className="card stats-card">
      <h3>📊 Statistics</h3>
      
      {/* Key Metrics Row */}
      <div className="metrics-row">
        <div className="metric">
          <span className="metric-value">{stats.completed_tests}</span>
          <span className="metric-label">Completed</span>
        </div>
        <div className="metric-divider" />
        <div className="metric">
          <span className="metric-value accent">{hasJudgments ? js.average?.toFixed(1) : '--'}</span>
          <span className="metric-label">Avg Score</span>
        </div>
        <div className="metric-divider" />
        <div className="metric">
          <span className="metric-value">{js?.count ?? 0}</span>
          <span className="metric-label">Judgments</span>
        </div>
      </div>

      {/* Score Distribution */}
      {hasJudgments && (
        <div className="score-section">
          <div className="score-range">
            <span className="range-label">Harmfulness Score Distribution</span>
          </div>
          
          <div className="distribution-visual">
            <div className="dist-bar-container five-ranges">
              <div className="dist-bar r1" style={{ width: getBarWidth(js.range_1_2, js.count) }}>
                {js.range_1_2 > 0 && <span>{js.range_1_2}</span>}
              </div>
              <div className="dist-bar r2" style={{ width: getBarWidth(js.range_3_4, js.count) }}>
                {js.range_3_4 > 0 && <span>{js.range_3_4}</span>}
              </div>
              <div className="dist-bar r3" style={{ width: getBarWidth(js.range_5_6, js.count) }}>
                {js.range_5_6 > 0 && <span>{js.range_5_6}</span>}
              </div>
              <div className="dist-bar r4" style={{ width: getBarWidth(js.range_7_8, js.count) }}>
                {js.range_7_8 > 0 && <span>{js.range_7_8}</span>}
              </div>
              <div className="dist-bar r5" style={{ width: getBarWidth(js.range_9_10, js.count) }}>
                {js.range_9_10 > 0 && <span>{js.range_9_10}</span>}
              </div>
            </div>
            <div className="dist-labels five-ranges">
              <span>1-2</span>
              <span>3-4</span>
              <span>5-6</span>
              <span>7-8</span>
              <span>9-10</span>
            </div>
          </div>
        </div>
      )}

      {/* Behavior Status */}
      <div className="behavior-status">
        <div className="status-row">
          <span className="status-dot completed" />
          <span className="status-text">{stats.behaviors_completed} Completed</span>
          <span className="status-bar">
            <span className="bar-fill completed" style={{ width: getBarWidth(stats.behaviors_completed, stats.total_behaviors) }} />
          </span>
        </div>
        <div className="status-row">
          <span className="status-dot in-progress" />
          <span className="status-text">{stats.behaviors_in_progress} In Progress</span>
          <span className="status-bar">
            <span className="bar-fill in-progress" style={{ width: getBarWidth(stats.behaviors_in_progress, stats.total_behaviors) }} />
          </span>
        </div>
        <div className="status-row">
          <span className="status-dot pending" />
          <span className="status-text">{stats.behaviors_pending} Pending</span>
          <span className="status-bar">
            <span className="bar-fill pending" style={{ width: getBarWidth(stats.behaviors_pending, stats.total_behaviors) }} />
          </span>
        </div>
      </div>
    </div>
  );
}

