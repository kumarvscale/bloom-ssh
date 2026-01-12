import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getBehaviors } from '../api/client';
import type { BehaviorSummary } from '../api/client';

export function Behaviors() {
  const [behaviors, setBehaviors] = useState<BehaviorSummary[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = filter !== 'all' ? { status: filter } : {};
      const res = await getBehaviors(params);
      setBehaviors(res.data);
    } catch (err) {
      setError('Failed to fetch behaviors');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filter]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✓';
      case 'in_progress': return '▶';
      case 'partial': return '◐';
      default: return '○';
    }
  };

  return (
    <div className="page behaviors">
      <div className="page-header">
        <h1>Behaviors</h1>
        <div className="filter-buttons">
          {['all', 'completed', 'in_progress', 'pending'].map((f) => (
            <button
              key={f}
              className={`filter-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="loading">Loading...</div>
      ) : behaviors.length === 0 ? (
        <div className="empty-state">No behaviors found</div>
      ) : (
        <div className="behaviors-grid">
          {behaviors.map((behavior) => (
            <div key={behavior.name} className={`behavior-card ${behavior.status}`}>
              <div className="behavior-header">
                <span className="status-icon">{getStatusIcon(behavior.status)}</span>
                <h3>{behavior.name}</h3>
              </div>
              
              <p className="behavior-path">{behavior.path}</p>
              <p className="behavior-definition">
                {behavior.definition.slice(0, 150)}
                {behavior.definition.length > 150 ? '...' : ''}
              </p>
              
              <div className="behavior-progress">
                <div className="turn-indicators">
                  {Array.from({ length: behavior.total_turns }, (_, i) => {
                    const turnNum = i + 4; // turns start at 4
                    const isComplete = behavior.completed_turns.includes(turnNum);
                    return (
                      <span 
                        key={i} 
                        className={`turn-dot ${isComplete ? 'complete' : ''}`}
                        title={`${turnNum} turns`}
                      />
                    );
                  })}
                </div>
                <span className="turn-count">
                  {behavior.completed_turns.length}/{behavior.total_turns}
                </span>
              </div>

              {behavior.has_results && (
                <Link 
                  to={`/conversations?behavior=${behavior.name}`}
                  className="view-results"
                >
                  View Results →
                </Link>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

