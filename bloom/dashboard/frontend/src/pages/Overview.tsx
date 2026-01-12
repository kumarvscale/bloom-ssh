import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getStatus, getStats, getConversations } from '../api/client';
import type { RunStatus, Stats, ConversationSummary } from '../api/client';
import { ProgressCard } from '../components/ProgressCard';
import { StatsCard } from '../components/StatsCard';
import { RunControlPanel } from '../components/RunControlPanel';

const POLL_INTERVAL = 5000; // 5 seconds

export function Overview() {
  const [status, setStatus] = useState<RunStatus | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [recent, setRecent] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [statusRes, statsRes, recentRes] = await Promise.all([
        getStatus(),
        getStats(),
        getConversations({ limit: 10 }),
      ]);
      setStatus(statusRes.data);
      setStats(statsRes.data);
      setRecent(recentRes.data);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to fetch data. Is the backend running?');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    fetchData();
    
    const interval = setInterval(fetchData, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchData]);

  const formatTime = (timestamp: string) => {
    if (!timestamp) return '--';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  if (loading) {
    return <div className="page loading">Loading...</div>;
  }

  const formatLastUpdated = () => {
    if (!lastUpdated) return '';
    return `Updated ${lastUpdated.toLocaleTimeString()}`;
  };

  return (
    <div className="page overview">
      <div className="page-header">
        <h1>SSH Behaviors Dashboard</h1>
        <span className="auto-refresh-indicator">
          <span className="pulse-dot" />
          Auto-refreshing • {formatLastUpdated()}
        </span>
      </div>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {/* Run Control Buttons */}
      <RunControlPanel 
        isRunning={status?.is_running || false} 
        onStatusChange={fetchData}
      />

      <div className="cards-row">
        <ProgressCard status={status} />
        <StatsCard stats={stats} />
      </div>

      <div className="card recent-section">
        <div className="card-header">
          <h3>Recent Conversations</h3>
          <Link to="/conversations" className="view-all">View all →</Link>
        </div>
        
        {recent.length === 0 ? (
          <p className="muted">No conversations yet</p>
        ) : (
          <table className="conversations-table">
            <thead>
              <tr>
                <th>Behavior</th>
                <th>Turns</th>
                <th>Stage</th>
                <th>Score</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((conv) => (
                <tr key={conv.id}>
                  <td>
                    <Link to={`/conversations/${conv.id}`} className="behavior-cell">
                      <span className="behavior-name">{conv.behavior}</span>
                      {conv.preview && (
                        <span className="behavior-preview">{conv.preview}</span>
                      )}
                    </Link>
                  </td>
                  <td>{conv.turn_count}</td>
                  <td>
                    <span className={`stage-badge ${conv.stage}`}>
                      {conv.stage}
                    </span>
                  </td>
                  <td>
                    {conv.score !== null ? conv.score.toFixed(2) : '--'}
                  </td>
                  <td className="muted">{formatTime(conv.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

