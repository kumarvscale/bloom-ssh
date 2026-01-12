import { useEffect, useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getRunHistory, getRunConversations } from '../api/client';
import type { DateGroup, HistoryConversation } from '../api/client';

export function History() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [dateGroups, setDateGroups] = useState<DateGroup[]>([]);
  const [conversations, setConversations] = useState<HistoryConversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedDates, setExpandedDates] = useState<Set<string>>(new Set());
  
  const selectedRunId = searchParams.get('run') || null;

  const fetchRuns = useCallback(async () => {
    try {
      setError(null);
      const res = await getRunHistory();
      setDateGroups(res.data);
      // Auto-expand the first date group
      if (res.data.length > 0) {
        setExpandedDates(new Set([res.data[0].date]));
      }
    } catch (err) {
      setError('Failed to fetch run history');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchConversations = useCallback(async (runId: string) => {
    try {
      setError(null);
      const res = await getRunConversations(runId);
      setConversations(res.data);
    } catch (err) {
      setError('Failed to fetch conversations');
      console.error(err);
    }
  }, []);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  useEffect(() => {
    if (selectedRunId) {
      fetchConversations(selectedRunId);
    } else {
      setConversations([]);
    }
  }, [selectedRunId, fetchConversations]);

  const selectRun = (runId: string) => {
    if (runId === selectedRunId) {
      setSearchParams({});
    } else {
      setSearchParams({ run: runId });
    }
  };

  const toggleDateExpand = (date: string) => {
    setExpandedDates(prev => {
      const next = new Set(prev);
      if (next.has(date)) {
        next.delete(date);
      } else {
        next.add(date);
      }
      return next;
    });
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleString();
    } catch {
      return isoString;
    }
  };

  const totalRuns = dateGroups.reduce((sum, g) => sum + g.runs.length, 0);

  if (loading) {
    return <div className="page loading">Loading run history...</div>;
  }

  return (
    <div className="page history">
      <div className="page-header">
        <h1>📜 Run History</h1>
        <span className="muted">{totalRuns} runs across {dateGroups.length} days</span>
      </div>

      {error && (
        <div className="error-banner">{error}</div>
      )}

      <div className="history-layout">
        {/* Runs List */}
        <div className="runs-panel">
          <h3>All Runs</h3>
          {dateGroups.length === 0 ? (
            <p className="muted">No runs found. Start your first evaluation!</p>
          ) : (
            <div className="date-groups">
              {dateGroups.map((group) => (
                <div key={group.date} className="date-group">
                  <div 
                    className={`date-header ${expandedDates.has(group.date) ? 'expanded' : ''}`}
                    onClick={() => toggleDateExpand(group.date)}
                  >
                    <span className="expand-icon">{expandedDates.has(group.date) ? '▼' : '▶'}</span>
                    <span className="date-title">{group.date_display}</span>
                    <span className="date-stats">
                      {group.runs.length} run{group.runs.length !== 1 ? 's' : ''} • {group.total_conversations} convos
                    </span>
                  </div>
                  
                  {expandedDates.has(group.date) && (
                    <div className="runs-list">
                      {group.runs.map((run) => (
                        <div 
                          key={run.run_id}
                          className={`run-card ${selectedRunId === run.run_id ? 'selected' : ''}`}
                          onClick={() => selectRun(run.run_id)}
                        >
                          <div className="run-header">
                            <span className="run-time">
                              {run.run_id === 'default' ? '📁 Default' : `🕐 ${run.time_only}`}
                            </span>
                            {run.run_id === 'default' && (
                              <span className="run-badge default">Default</span>
                            )}
                          </div>
                          <div className="run-stats">
                            <span className="stat">
                              <span className="stat-value">{run.completed_tests}</span>
                              <span className="stat-label">done</span>
                            </span>
                            {run.failed_tests > 0 && (
                              <span className="stat failed">
                                <span className="stat-value">{run.failed_tests}</span>
                                <span className="stat-label">fail</span>
                              </span>
                            )}
                            <span className="stat">
                              <span className="stat-value">{run.conversation_count}</span>
                              <span className="stat-label">convos</span>
                            </span>
                          </div>
                          {run.config && Object.keys(run.config).length > 0 && (
                            <div className="run-config">
                              {run.config.target_model && (
                                <span className="config-tag" title="Target Model">
                                  🎯 {run.config.target_model}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Conversations Panel */}
        <div className="conversations-panel">
          {selectedRunId ? (
            <>
              <h3>Conversations from: {selectedRunId === 'default' ? 'Default Results' : selectedRunId}</h3>
              {conversations.length === 0 ? (
                <p className="muted">No conversations in this run</p>
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
                    {conversations.map((conv) => (
                      <tr key={conv.id}>
                        <td>
                          <Link 
                            to={`/history/conversation/${encodeURIComponent(conv.id)}`}
                            className="behavior-cell"
                          >
                            <span className="behavior-name">{conv.behavior}</span>
                            {conv.preview && (
                              <span className="behavior-preview">{conv.preview}</span>
                            )}
                          </Link>
                        </td>
                        <td>{conv.turn_count || '-'}</td>
                        <td>
                          <span className={`stage-badge ${conv.stage}`}>
                            {conv.stage}
                          </span>
                        </td>
                        <td>
                          {conv.score !== null ? conv.score.toFixed(2) : '--'}
                        </td>
                        <td className="muted">{formatDate(conv.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          ) : (
            <div className="select-run-prompt">
              <span className="prompt-icon">👈</span>
              <p>Select a run from the list to view its conversations</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

