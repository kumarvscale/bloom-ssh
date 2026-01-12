import { useEffect, useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getConversations } from '../api/client';
import type { ConversationSummary } from '../api/client';

const POLL_INTERVAL = 5000; // 5 seconds

export function Conversations() {
  const [searchParams] = useSearchParams();
  const behaviorFilter = searchParams.get('behavior');
  
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      if (conversations.length === 0) setLoading(true);
      setError(null);
      const params: { limit: number; behavior?: string } = { limit: 100 };
      if (behaviorFilter) {
        params.behavior = behaviorFilter;
      }
      const res = await getConversations(params);
      setConversations(res.data);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to fetch conversations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [behaviorFilter, conversations.length]);

  useEffect(() => {
    fetchData();
    
    const interval = setInterval(fetchData, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [behaviorFilter]);

  const formatTime = (timestamp: string) => {
    if (!timestamp) return '--';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getStageIcon = (stage: string) => {
    switch (stage) {
      case 'understanding': return '🔍';
      case 'ideation': return '💡';
      case 'rollout': return '🎭';
      case 'judgment': return '⚖️';
      default: return '○';
    }
  };

  const formatLastUpdated = () => {
    if (!lastUpdated) return '';
    return `Updated ${lastUpdated.toLocaleTimeString()}`;
  };

  return (
    <div className="page conversations">
      <div className="page-header">
        <h1>
          Conversations
          {behaviorFilter && (
            <span className="filter-label">
              for {behaviorFilter}
              <Link to="/conversations" className="clear-filter">×</Link>
            </span>
          )}
        </h1>
        <span className="auto-refresh-indicator">
          <span className="pulse-dot" />
          Auto-refreshing • {formatLastUpdated()}
        </span>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="loading">Loading...</div>
      ) : conversations.length === 0 ? (
        <div className="empty-state">
          No conversations found
          {behaviorFilter && (
            <Link to="/conversations" className="link">View all conversations</Link>
          )}
        </div>
      ) : (
        <table className="conversations-table full">
          <thead>
            <tr>
              <th>Behavior</th>
              <th>Turns</th>
              <th>Stage</th>
              <th>Score</th>
              <th>Timestamp</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {conversations.map((conv) => (
              <tr key={conv.id}>
                <td className="behavior-cell">
                  <Link to={`/conversations/${conv.id}`}>
                    {conv.behavior}
                  </Link>
                </td>
                <td>{conv.turn_count}</td>
                <td>
                  <span className={`stage-badge ${conv.stage}`}>
                    {getStageIcon(conv.stage)} {conv.stage}
                  </span>
                </td>
                <td className={conv.score !== null ? 'has-score' : 'no-score'}>
                  {conv.score !== null ? conv.score.toFixed(2) : '--'}
                </td>
                <td className="muted">{formatTime(conv.timestamp)}</td>
                <td>
                  <Link to={`/conversations/${conv.id}`} className="view-link">
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

